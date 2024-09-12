#!/usr/bin/env node

const express = require('express');
const path = require('path');
// const escapeHtml = require('escape-html');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');
const db = require('./db'); 

// Routes
const indexRoute = require('./routes/index');
app.use('/', indexRoute);

const BatchesRoute = require('./routes/batches');
app.use('/batches', BatchesRoute);

const BatchSummariesRoute = require('./routes/batch_summaries');
app.use('/batches/summaries', BatchSummariesRoute);

const PackagesRoute = require('./routes/packages');
app.use('/packages', PackagesRoute);

// About route
app.get('/about', (req, res) => {
  res.render('pages/about', { title: 'About Us' });
});

// 404 - Not Found
app.use((req, res, next) => {
    res.status(404).render('pages/404', { title: 'Page Not Found' });
  });  

// 500 - Server Error handler
app.use((err, req, res, next) => {
    console.error(err.stack); // Log the error
    res.status(500).render('pages/500', { title: 'Server Error' }); // Correct path to the 500 view
  });

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`); // Changed log for maturity
});