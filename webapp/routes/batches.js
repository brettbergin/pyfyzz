#!/usr/bin/env node

const express = require('express');
// const escapeHtml = require('escape-html');
const { spawn } = require('child_process');

const router = express.Router();
const db = require('../db'); 

router.get('/', async (req, res) => {
    const { batch_job_id, package_to_scan, sort = 'discovered_methods', order = 'DESC' } = req.query;

    try {
      let query = 'SELECT * FROM batches';
      const queryParams = [];

      // If batch_job_id is provided, filter by it
      if (batch_job_id) {
        query += ' WHERE batch_job_id = ?';
        queryParams.push(batch_job_id);
      }

      query += ` ORDER BY ${sort} ${order.toUpperCase()}`;

      const [batches] = await db.query(query, queryParams);

      // Scan the package if provided
      if (package_to_scan) {        
        const pyfyzz = spawn('pyfyzz', ['-p', package_to_scan, '-o', 'json', '-i']);

        pyfyzz.stdout.on('data', (data) => {
          console.log(`Output:\n${data}`);
        });

        pyfyzz.stderr.on('data', (data) => {
          console.error(`Error:\n${data}`);
        });

        pyfyzz.on('close', (code) => {
          console.log(`Process exited with code ${code}`);
          res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches,
            sort,    // Pass current sort field
            order,   // Pass current order
            error: null
          });
        });

      } else {
        res.render('pages/batches', {
          title: `Batch for Job(s): ${batch_job_id || 'All'}`,
          batches,
          sort,    // Pass current sort field
          order,   // Pass current order
          error: null
        });
      }

    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', {
        title: 'Server Error', 
        error: 'Something went wrong!'
      });
    }
});

router.post('/', async (req, res) => {
    const { batch_job_id, package_to_scan, sort = 'exception_occurences', order = 'DESC'} = req.body;
    const cleaned_package = `${package_to_scan}`;
    
    try {
      let query = 'SELECT * FROM batches';
      const queryParams = [];

      if (batch_job_id) {
        query += ' WHERE batch_job_id = ?';
        queryParams.push(batch_job_id);
      }
      const [batches] = await db.query(query, queryParams);

      if (cleaned_package) {        
        const pyfyzz = spawn('pyfyzz', ['-p', cleaned_package, '-o', 'json', '-i']);

        pyfyzz.stdout.on('data', (data) => {
          console.log(`Output:\n${data}`);
        });

        pyfyzz.stderr.on('data', (data) => {
          console.error(`Error:\n${data}`);
        });

        pyfyzz.on('close', (code) => {
          console.log(`Process exited with code ${code}`);
        });
      };

      res.render('pages/batches', {
        title: `Batch for Job ID ${batch_job_id || 'All'}`,
        batches,
        error: null,
        sort: sort,
        order: order
      });

    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error', error: 'Something went wrong!' });
    }
});

module.exports = router;
