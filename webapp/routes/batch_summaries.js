#!/usr/bin/env node

const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC' } = req.query;

    try {
        let query = 'SELECT * FROM batch_summaries';
        const queryParams = [];

        if (batch_job_id) {
            query += ' WHERE batch_job_id = ?';
            queryParams.push(batch_job_id);
        }

        query += ` ORDER BY ${sort} ${order.toUpperCase()}`;

        const [summaries] = await db.query(query, queryParams);

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Job ID ${batch_job_id || 'All'}`,
            summaries,
            sort,
            order,
            error: null
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
            error: errorMessage
        });
    }
});

router.post('/', async (req, res) => {
    const { package_name } = req.body;
    const { batch_job_id, sort = 'exception_occurences', order = 'DESC' } = req.query;

    try {
        let query = 'SELECT * FROM batch_summaries';
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

        query += ` ORDER BY ${sort} ${order.toUpperCase()}`;

        const [summaries] = await db.query(query, queryParams);

        res.render('pages/batch_summaries', {
            title: `Batch Summaries for Package ${package_name || 'All'}`,
            summaries,
            sort,
            order,
            error: null
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
            error: errorMessage
        });
    }
});

module.exports = router;
