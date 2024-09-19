#!/usr/bin/env node

const express = require('express');
// const escapeHtml = require('escape-html');

const router = express.Router();
const db = require('../db'); 

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC' } = req.query; // Default sorting

    try {
      let query = 'SELECT * FROM batch_summaries';
      const queryParams = [];

      // If batch_job_id is provided, filter by it
      if (batch_job_id) {
        query += ' WHERE batch_job_id = ?';
        queryParams.push(batch_job_id);
      }

      // Add sorting to the query
      query += ` ORDER BY ${sort} ${order.toUpperCase()}`;

      // Execute the query
      const [summaries] = await db.query(query, queryParams);

      res.render('pages/batch_summaries', {
        title: `Batch Summaries for Job ID ${batch_job_id || 'All'}`,
        summaries,
        sort,
        order
      });
    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

router.post('/', async (req, res) => {
    const { package_name } = req.body;
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC' } = req.query; // Default sorting

    try {
        let query = 'SELECT * FROM batch_summaries';
        const queryParams = [];

        // If batch_job_id is provided, filter by it
        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        // If package_name is provided, add a condition for it
        if (package_name) {
            query += batch_job_id ? ' AND' : ' WHERE';
            query += ' package_name LIKE ?';
            queryParams.push(`%${package_name}%`);
        }

        const [summaries] = await db.query(query, queryParams);

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Package ${package_name || 'All'}`,
            summaries,
            sort,
            order
        });
    } catch (error) {
        console.error(error);
        res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

module.exports = router;
