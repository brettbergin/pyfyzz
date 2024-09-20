#!/usr/bin/env node

const express = require('express');
const { spawn } = require('child_process');

const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'discovered_methods', order = 'DESC' } = req.query;

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

        res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches,
            sort,
            order,
            error: null  // No error if query succeeds
        });
    } catch (error) {
        console.error(error);

        let errorMessage = 'Something went wrong!';
        if (error.code === 'ER_NO_SUCH_TABLE') {
            errorMessage = 'Database table "batches" does not exist. Please check your database schema.';
        }

        res.render('pages/batches', {
            title: `Batch for Job(s): ${batch_job_id || 'All'}`,
            batches: [], // Empty array in case of error
            sort,
            order,
            error: errorMessage
        });
    }
});

router.post('/', async (req, res) => {
    const { package_to_scan } = req.body;
    const { batch_job_id, sort = 'discovered_methods', order = 'DESC' } = req.query;

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
                    error: null
                });
            });
        } else {
            res.render('pages/batches', {
                title: `Batch for Job(s): ${batch_job_id || 'All'}`,
                batches,
                sort,
                order,
                error: null
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
            batches: [], // Empty array in case of error
            sort,
            order,
            error: errorMessage
        });
    }
});

module.exports = router;
