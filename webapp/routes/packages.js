#!/usr/bin/env node

const express = require('express');
const { marked } = require('marked');

const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'name', order = 'DESC', page = 1, limit = 10 } = req.query; // Pagination defaults
    const offset = (page - 1) * limit;  // Calculate offset for pagination

    try {
        let query = 'SELECT SQL_CALC_FOUND_ROWS * FROM package_records';
        const queryParams = [];

        // If batch_job_id is provided, filter by it
        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        // Add sorting to the query
        query += ` ORDER BY ${sort} ${order.toUpperCase()} LIMIT ? OFFSET ?`;
        queryParams.push(parseInt(limit), parseInt(offset)); // Add limit and offset for pagination

        // Execute the query
        const [packages] = await db.query(query, queryParams);
        const [[{ totalRows }]] = await db.query('SELECT FOUND_ROWS() AS totalRows'); // Get total number of rows

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
            error: null,
            page: parseInt(page),
            totalRows,
            limit: parseInt(limit)
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
            error: errorMessage,
            page: parseInt(page),
            totalRows: 0,
            limit: parseInt(limit)
        });
    }
});

module.exports = router;
