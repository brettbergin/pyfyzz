#!/usr/bin/env node

const express = require('express');
const escapeHtml = require('escape-html');

const router = express.Router();
const db = require('../db'); 


router.get('/', async (req, res) => {
    const { batch_job_id, package_name, sort = 'package_name', order = 'DESC' } = req.query;
    const allowedSortFields = ['package_name', 'start_time', 'stop_time', 'discovered_methods'];
    const sanitizedSort = allowedSortFields.includes(sort) ? sort : 'package_name';
    const sanitizedOrder = ['ASC', 'DESC'].includes(order?.toUpperCase()) ? order.toUpperCase() : 'DESC';

    try {
        // First query to fetch batch and exception details
        let query1 = `
          SELECT 
            b.batch_job_id, 
            b.package_name,
            COALESCE(pr.version, 'Unknown') AS version,
            b.start_time,
            b.stop_time,
            b.batch_status,
            b.discovered_methods,
            b.discovered_methods_date,
            pr.home_page,
            pr.project_url,
            pr.project_urls,
            GROUP_CONCAT(bs.exception_type ORDER BY bs.exception_occurences DESC SEPARATOR ', ') AS Exceptions,
            GROUP_CONCAT(CONCAT(bs.exception_type, '(', bs.exception_occurences, ') ') ORDER BY bs.exception_occurences DESC SEPARATOR ', ') AS ExceptionCount
          FROM pyfyzz.batches b
          JOIN pyfyzz.batch_summaries bs
            ON b.batch_job_id = bs.batch_job_id
          LEFT JOIN pyfyzz.package_records pr
            ON b.batch_job_id = pr.batch_job_id 
            AND b.package_name = pr.name
        `;
        
        const queryParams1 = [];
      
        if (package_name) {
          query1 += `
            WHERE b.start_time = (
              SELECT MAX(b2.start_time) 
              FROM pyfyzz.batches b2 
              WHERE b2.package_name = b.package_name
            ) 
            AND b.package_name LIKE ?`;
          queryParams1.push(`%${package_name}%`);
        } else {
          query1 += `
            WHERE b.start_time = (
              SELECT MAX(b2.start_time) 
              FROM pyfyzz.batches b2 
              WHERE b2.package_name = b.package_name
            )`;
        }
      
      query1 += ` GROUP BY b.batch_job_id, pr.version, pr.home_page, pr.project_url, pr.project_urls ORDER BY ${sort} ${order};`;

      // Second query to fetch topologies and module information
      let query2 = `
          SELECT 
            b.batch_job_id, 
            b.package_name,
            COALESCE(pr.name, 'Unknown') AS package_name,
            COUNT(DISTINCT t.module_name) AS ModulesCount,
            GROUP_CONCAT(DISTINCT t.module_name ORDER BY t.module_name DESC SEPARATOR ', ') AS Modules,
            COUNT(DISTINCT t.class_name) AS ClassesCount,
            GROUP_CONCAT(DISTINCT t.class_name ORDER BY t.class_name DESC SEPARATOR ', ') AS Classes,
            COUNT(DISTINCT t.method_name) AS MethodsCount,
            GROUP_CONCAT(DISTINCT t.method_name ORDER BY t.method_name DESC SEPARATOR ', ') AS Methods
          FROM pyfyzz.batches b
          LEFT JOIN pyfyzz.package_records pr
            ON b.batch_job_id = pr.batch_job_id 
            AND b.package_name = pr.name
          LEFT JOIN pyfyzz.topologies t
            ON b.batch_job_id = t.batch_job_id
            AND b.package_name = t.package_name
          GROUP BY b.batch_job_id, b.package_name, pr.name
          ORDER BY b.start_time DESC;
      `;

      const queryParams2 = [];

      // Third query to fetch fuzz results information
      let query3 = `
        SELECT
          fr.record_id,
          b.batch_job_id, 
          b.package_name,
          pr.name,
          fr.method_name as FuzzedMethods,
          fr.encoded_source as EncodedSource,
          fr.improved_source as ImprovedEncodedSource,
          fr.exception_traceback as EncodedTraceback,
          fr.exception as ExceptionMessage,
          fr.inputs as ExceptionInputs,
          fr.exception_type as ExceptionType,
          fr.is_python_exception as IsPythonException
        FROM pyfyzz.batches b
        LEFT JOIN pyfyzz.package_records pr
        ON b.batch_job_id = pr.batch_job_id 
        AND b.package_name = pr.name
        LEFT JOIN pyfyzz.fuzz_results fr
        ON b.batch_job_id = fr.batch_job_id
        AND b.package_name = fr.package_name
        WHERE fr.is_python_exception = 1
        GROUP BY
          fr.record_id,
          b.batch_job_id, 
          b.package_name,
          pr.name,
            fr.method_name,
          fr.exception, 
          fr.inputs,
          fr.encoded_source,
          fr.improved_source,
            fr.exception_traceback,
          fr.exception_type,
          fr.is_python_exception
        ORDER BY fr.method_name DESC;
      `;

      const queryParams3 = [];

      const [results1, results2, results3] = await Promise.all([
          db.query(query1, queryParams1),
          db.query(query2, queryParams2),
          db.query(query3, queryParams3)
      ]);

      if (results1.status === "rejected") {
        throw new Error(`Error fetching batch and exception details: ${results1.reason}`);
      }
      if (results2.status === "rejected") {
        throw new Error(`Error fetching module and topology info: ${results2.reason}`);
      }
      if (results3.status === "rejected") {
        throw new Error(`Error fetching fuzz results: ${results3.reason}`);
      }
      else {
      };

      results3[0].forEach(result => {
        if (result.EncodedSource) {
            try {
                const decoded = Buffer.from(result.EncodedSource, 'base64').toString('utf-8');
                result.DecodedSource = escapeHtml(decoded);
            } catch (e) {
                result.DecodedSource = 'Source Code Unknown';
            }
        } else {
            result.DecodedSource = 'No Source Available';
        }
      });

      results3[0].forEach(result => {
        if (result.ImprovedEncodedSource) {
            try {
                const decoded = Buffer.from(result.ImprovedEncodedSource, 'base64').toString('utf-8');
                result.DecodedImprovedSource = escapeHtml(decoded);
            } catch (e) {
                result.DecodedImprovedSource = 'Improved Source Unknown';
            }
        } else {
            result.DecodedImprovedSource = 'No Improved Source Available';
        }
      });

      results3[0].forEach(result => {
        if (result.EncodedTraceback) {
            try {
                const decoded = Buffer.from(result.EncodedTraceback, 'base64').toString('utf-8');
                result.DecodedTraceback = escapeHtml(decoded);
            } catch (e) {
                result.DecodedTraceback = 'Full Traceback Unknown';
            }
        } else {
            result.DecodedTraceback = 'No Traceback Available';
        }
      });
      
      res.render('pages/home', {
          title: 'PyFyzz Home',
          results1: results1[0],
          results2: results2[0],
          results3: results3[0],
          sort: sanitizedSort,
          order: sanitizedOrder,
          package_name: package_name || '',
          batch_job_id: batch_job_id || ''
      });

    } catch (error) {
        console.error('Error executing queries:', error);
        res.status(500).render('pages/500', { title: 'Server Error', error: 'Something went wrong!' });
    }
});

module.exports = router;