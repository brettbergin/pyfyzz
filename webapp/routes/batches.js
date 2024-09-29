#!/usr/bin/env node

const express = require('express');
const { spawn } = require('child_process');

const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'discovered_methods', order = 'DESC', page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;  // Calculate offset for pagination

    try {
        let query = 'SELECT SQL_CALC_FOUND_ROWS * FROM batches';
        const queryParams = [];

        // If batch_job_id is provided, filter by it
        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        query += ` ORDER BY ${sort} ${order.toUpperCase()} LIMIT ? OFFSET ?`;
        queryParams.push(parseInt(limit), parseInt(offset)); // Limit and offset for pagination

        const [batches] = await db.query(query, queryParams);
        const [[{ totalRows }]] = await db.query('SELECT FOUND_ROWS() AS totalRows'); // Get total number of rows

        res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches,
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
            errorMessage = 'Database table "batches" does not exist. Please check your database schema.';
        }

        res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches: [],
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
    const { package_to_scan } = req.body;
    const { batch_job_id, sort = 'discovered_methods', order = 'DESC', page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;  // Calculate offset for pagination

    try {
        let query = 'SELECT SQL_CALC_FOUND_ROWS * FROM batches';
        const queryParams = [];

        // If batch_job_id is provided, filter by it
        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        query += ` ORDER BY ${sort} ${order.toUpperCase()} LIMIT ? OFFSET ?`;
        queryParams.push(parseInt(limit), parseInt(offset)); // Limit and offset for pagination

        const [batches] = await db.query(query, queryParams);
        const [[{ totalRows }]] = await db.query('SELECT FOUND_ROWS() AS totalRows'); // Get total number of rows

        // If package_to_scan is provided, launch the PyFyzz scan
        if (package_to_scan) {
            const pyfyzz = spawn('pyfyzz', ['scan', '-p', package_to_scan]);

            pyfyzz.stdout.on('data', (data) => {
                console.log(`PyFyzz Output: ${data}`);
            });

            pyfyzz.stderr.on('data', (data) => {
                console.error(`PyFyzz Error: ${data}`);
            });

            pyfyzz.on('close', (code) => {
                console.log(`PyFyzz process exited with code ${code}`);
                res.render('pages/batches', {
                    title: `Batch for Job(s): ${batch_job_id || 'All'}`,
                    batches,
                    sort,
                    order,
                    error: null,
                    page: parseInt(page),
                    totalRows,
                    limit: parseInt(limit)
                });
            });
        } else {
            res.render('pages/batches', {
                title: `Batch for Job(s): ${batch_job_id || 'All'}`,
                batches,
                sort,
                order,
                error: null,
                page: parseInt(page),
                totalRows,
                limit: parseInt(limit)
            });
        }
    } catch (error) {
        console.error(error);

        let errorMessage = 'Something went wrong!';
        if (error.code === 'ER_NO_SUCH_TABLE') {
            errorMessage = 'Database table "batches" does not exist. Please check your database schema.';
        }

        res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches: [],
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
