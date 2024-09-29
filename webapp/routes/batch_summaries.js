#!/usr/bin/env node

const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC', page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;  // Calculate offset for pagination

    try {
        let query = 'SELECT SQL_CALC_FOUND_ROWS * FROM batch_summaries';
        const queryParams = [];

        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        query += ` ORDER BY ${sort} ${order.toUpperCase()} LIMIT ? OFFSET ?`;
        queryParams.push(parseInt(limit), parseInt(offset)); // Limit and offset for pagination

        // Execute the query and also get the total number of rows found
        const [summaries] = await db.query(query, queryParams);
        const [[{ totalRows }]] = await db.query('SELECT FOUND_ROWS() AS totalRows'); // Get total number of rows

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Job ID ${batch_job_id || 'All'}`,
            summaries,
            sort,
            order,
            error: null,
            page: parseInt(page),
            totalRows,
            limit: parseInt(limit)
        });
    } catch (error) {
        console.error("ERROR:::", error);

        let errorMessage = 'Something went wrong!';
        if (error.code === 'ER_NO_SUCH_TABLE') {
            errorMessage = 'Database table "batch_summaries" does not exist. Please check your database schema.';
        }

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Job ID ${batch_job_id || 'All'}`,
            summaries: [], // Empty array in case of error
            sort,
            order,
            error: errorMessage,
            page: parseInt(page),
            totalRows: 0,
            limit: parseInt(limit)
        });
    }
});

router.post('/', async (req, res) => {
    const { package_name } = req.body;
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC', page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;  // Calculate offset for pagination

    try {
        let query = 'SELECT SQL_CALC_FOUND_ROWS * FROM batch_summaries';
        const queryParams = [];

        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        if (package_name) {
            query += batch_job_id ? ' AND' : ' WHERE';
            query += ' package_name LIKE ?';
            queryParams.push(`%${package_name}%`);
        }

        query += ` ORDER BY ${sort} ${order.toUpperCase()} LIMIT ? OFFSET ?`;
        queryParams.push(parseInt(limit), parseInt(offset)); // Limit and offset for pagination

        // Execute the query and also get the total number of rows found
        const [summaries] = await db.query(query, queryParams);
        const [[{ totalRows }]] = await db.query('SELECT FOUND_ROWS() AS totalRows'); // Get total number of rows

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Package ${package_name || 'All'}`,
            summaries,
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
            errorMessage = 'Database table "batch_summaries" does not exist. Please check your database schema.';
        }

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Package ${package_name || 'All'}`,
            summaries: [], // Empty array in case of error
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
