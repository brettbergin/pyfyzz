const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const escapeHtml = require('escape-html');
require('dotenv').config();
const marked = require('marked');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');
const db = require('./db'); 

// // Routes
// const indexRoute = require('./routes/index');
// app.use('/', indexRoute);

app.get('/batches', async (req, res) => {
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
            title: `Batch for Job ID ${batch_job_id || 'All'}`,
            batches,
            sort,    // Pass current sort field
            order,   // Pass current order
            error: null
          });
        });

      } else {
        res.render('pages/batches', {
          title: `Batch for Job ID ${batch_job_id || 'All'}`,
          batches,
          sort,    // Pass current sort field
          order,   // Pass current order
          error: null
        });
      }

    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error', error: 'Something went wrong!' });
    }
});

app.post('/batches', async (req, res) => {
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

app.get('/batches/summaries', async (req, res) => {
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
      query += ` ORDER BY ${sort} ${order.toUpperCase()}`;  // Prevent SQL injection

      // Execute the query
      const [summaries] = await db.query(query, queryParams);

      res.render('pages/batch_summaries', {
        title: `Batch Summaries for Job ID ${batch_job_id || 'All'}`,
        summaries,
        sort,   // Pass current sort field
        order   // Pass current order
      });
    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

app.post('/batches/summaries', async (req, res) => {
    const { package_name } = req.body;  // Get package_name from form submission
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
            queryParams.push(`%${package_name}%`);  // Use LIKE for partial match
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

app.get('/packages', async (req, res) => {
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
            // Leave description as it is in case of an error
          }
        }
      });

      res.render('pages/packages', {
        title: `Package Info`,
        packages,
        sort,    // Pass current sort field
        order    // Pass current order
      });
    } catch (error) {
      console.error(error);
      res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

app.get('/', async (req, res) => {
    const { batch_job_id, package_name, sort = 'package_name', order = 'DESC' } = req.query;
    const allowedSortFields = ['package_name', 'start_time', 'stop_time', 'discovered_methods'];
    const sanitizedSort = allowedSortFields.includes(sort) ? sort : 'package_name';
    const sanitizedOrder = ['ASC', 'DESC'].includes(order?.toUpperCase()) ? order.toUpperCase() : 'DESC';

    try {
        // First query to fetch batch and exception details
        let query1 = `
          SELECT 
            b.batch_job_id, 
            b.package_name,
            COALESCE(pr.version, 'Unknown') AS version,
            b.start_time,
            b.stop_time,
            b.batch_status,
            b.discovered_methods,
            b.discovered_methods_date,
            pr.home_page,
            pr.project_url,
            pr.project_urls,
            GROUP_CONCAT(bs.exception_type ORDER BY bs.exception_occurences DESC SEPARATOR ', ') AS Exceptions,
            GROUP_CONCAT(CONCAT(bs.exception_type, '(', bs.exception_occurences, ') ') ORDER BY bs.exception_occurences DESC SEPARATOR ', ') AS ExceptionCount
          FROM pyfyzz.batches b
          JOIN pyfyzz.batch_summaries bs
            ON b.batch_job_id = bs.batch_job_id
          LEFT JOIN pyfyzz.package_records pr
            ON b.batch_job_id = pr.batch_job_id 
            AND b.package_name = pr.name
        `;
        
        const queryParams1 = [];
      
        if (package_name) {
          query1 += `
            WHERE b.start_time = (
              SELECT MAX(b2.start_time) 
              FROM pyfyzz.batches b2 
              WHERE b2.package_name = b.package_name
            ) 
            AND b.package_name LIKE ?`;
          queryParams1.push(`%${package_name}%`);
        } else {
          query1 += `
            WHERE b.start_time = (
              SELECT MAX(b2.start_time) 
              FROM pyfyzz.batches b2 
              WHERE b2.package_name = b.package_name
            )`;
        }
      
      query1 += ` GROUP BY b.batch_job_id, pr.version, pr.home_page, pr.project_url, pr.project_urls ORDER BY ${sort} ${order};`;

      // Second query to fetch topologies and module information
      let query2 = `
          SELECT 
            b.batch_job_id, 
            b.package_name,
            COALESCE(pr.name, 'Unknown') AS package_name,
            COUNT(DISTINCT t.module_name) AS ModulesCount,
            GROUP_CONCAT(DISTINCT t.module_name ORDER BY t.module_name DESC SEPARATOR ', ') AS Modules,
            COUNT(DISTINCT t.class_name) AS ClassesCount,
            GROUP_CONCAT(DISTINCT t.class_name ORDER BY t.class_name DESC SEPARATOR ', ') AS Classes,
            COUNT(DISTINCT t.method_name) AS MethodsCount,
            GROUP_CONCAT(DISTINCT t.method_name ORDER BY t.method_name DESC SEPARATOR ', ') AS Methods
          FROM pyfyzz.batches b
          LEFT JOIN pyfyzz.package_records pr
            ON b.batch_job_id = pr.batch_job_id 
            AND b.package_name = pr.name
          LEFT JOIN pyfyzz.topologies t
            ON b.batch_job_id = t.batch_job_id
            AND b.package_name = t.package_name
          GROUP BY b.batch_job_id, b.package_name, pr.name
          ORDER BY b.start_time DESC;
      `;

      const queryParams2 = [];

      // Third query to fetch fuzz results information
      let query3 = `
        SELECT 
          b.batch_job_id, 
          b.package_name,
          pr.name,
          fr.method_name as FuzzedMethods,
          fr.encoded_source as EncodedSource,
          fr.improved_source as ImprovedEncodedSource,
          fr.exception_traceback as EncodedTraceback,
          fr.exception as ExceptionMessage,
          fr.inputs as ExceptionInputs,
          fr.exception_type as ExceptionType,
          fr.is_python_exception as IsPythonException
        FROM pyfyzz.batches b
        LEFT JOIN pyfyzz.package_records pr
        ON b.batch_job_id = pr.batch_job_id 
        AND b.package_name = pr.name
        LEFT JOIN pyfyzz.fuzz_results fr
        ON b.batch_job_id = fr.batch_job_id
        AND b.package_name = fr.package_name
        WHERE fr.is_python_exception = 1
        GROUP BY 
          b.batch_job_id, 
          b.package_name,
          pr.name,
            fr.method_name,
          fr.exception, 
          fr.inputs,
          fr.encoded_source,
          fr.improved_source,
            fr.exception_traceback,
          fr.exception_type,
          fr.is_python_exception
        ORDER BY fr.method_name DESC;
      `;

      const queryParams3 = [];

      // Run all three queries concurrently using Promise.all
      const [results1, results2, results3] = await Promise.all([
          db.query(query1, queryParams1),
          db.query(query2, queryParams2),
          db.query(query3, queryParams3)
      ]);

      if (results1.status === "rejected") {
        throw new Error(`Error fetching batch and exception details: ${results1.reason}`);
      }
      if (results2.status === "rejected") {
        throw new Error(`Error fetching module and topology info: ${results2.reason}`);
      }
      if (results3.status === "rejected") {
        throw new Error(`Error fetching fuzz results: ${results3.reason}`);
      }
      else {
      };

      results3[0].forEach(result => {
        if (result.EncodedSource) {
            try {
                const decoded = Buffer.from(result.EncodedSource, 'base64').toString('utf-8');
                result.DecodedSource = escapeHtml(decoded);
            } catch (e) {
                result.DecodedSource = 'Source Code Unknown';
            }
        } else {
            result.DecodedSource = 'No Source Available';
        }
      });

      results3[0].forEach(result => {
        if (result.ImprovedEncodedSource) {
            try {
                const decoded = Buffer.from(result.ImprovedEncodedSource, 'base64').toString('utf-8');
                result.DecodedImprovedSource = escapeHtml(decoded);
            } catch (e) {
                result.DecodedImprovedSource = 'Improved Source Unknown';
            }
        } else {
            result.DecodedImprovedSource = 'No Improved Source Available';
        }
      });

      results3[0].forEach(result => {
        if (result.EncodedTraceback) {
            try {
                const decoded = Buffer.from(result.EncodedTraceback, 'base64').toString('utf-8');
                result.DecodedTraceback = escapeHtml(decoded);
            } catch (e) {
                result.DecodedTraceback = 'Full Traceback Unknown';
            }
        } else {
            result.DecodedTraceback = 'No Traceback Available';
        }
      });
      
      // Pass all three results to the EJS template
      res.render('pages/home', {
          title: 'PyFyzz Home',
          results1: results1[0], // Results from the first query
          results2: results2[0], // Results from the second query
          results3: results3[0], // Results from the third query
          sort: sanitizedSort,
          order: sanitizedOrder,
          package_name: package_name || '', // Pass the current search term back to the template
          batch_job_id: batch_job_id || '' // Pass the batch_job_id if provided
      });

    } catch (error) {
        console.error('Error executing queries:', error);
        res.status(500).render('pages/500', { title: 'Server Error', error: 'Something went wrong!' });
    }
});


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