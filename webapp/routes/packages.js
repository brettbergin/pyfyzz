#!/usr/bin/env node

const express = require('express');
const { marked } = require('marked');
// const escapeHtml = require('escape-html');

const router = express.Router();
const db = require('../db'); 


router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'name', order = 'DESC' } = req.query; // Default sort by batch_job_id, ascending
    
    try {
      let query = 'SELECT * FROM package_records';
      const queryParams = [];
  
      // If batch_job_id is provided, filter by it
      if (batch_job_id) {
        query += ' WHERE batch_job_id = ?';
        queryParams.push(batch_job_id);
      }

      // Add sorting to the query
      query += ` ORDER BY ${sort} ${order.toUpperCase()}`;
  
      // Execute query and render the packages page
      const [packages] = await db.query(query, queryParams);

      // Process each package description with markdown
      packages.forEach(pkg => {
        if (pkg.description) {
          try {
            // Convert markdown to HTML
            pkg.description = marked(pkg.description);
          } catch (e) {
            console.error('Error parsing markdown:', e);
          }
        }
      });

      res.render('pages/packages', {
        title: `Package Info`,
        packages,
        sort,
        order
      });
    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

module.exports = router;
