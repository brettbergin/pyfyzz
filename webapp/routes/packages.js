#!/usr/bin/env node

const express = require('express');
const { marked } = require('marked');

const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'name', order = 'DESC' } = req.query; // Default sort by package name, descending

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

        // Execute the query
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
            order,
            error: null  // No error if query succeeds
        });
    } catch (error) {
        console.error(error);

        let errorMessage = 'Something went wrong!';
        if (error.code === 'ER_NO_SUCH_TABLE') {
            errorMessage = 'Database table "package_records" does not exist. Please check your database schema.';
        }

        res.render('pages/packages', {
            title: `Package Info`,
            packages: [],  // Empty array in case of error
            sort,
            order,
            error: errorMessage
        });
    }
});

module.exports = router;
