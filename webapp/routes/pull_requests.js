#!/usr/bin/env node

const express = require('express');
const { spawn } = require('child_process');

const router = express.Router();

router.get('/new', async (req, res) => {
    const { record_id = '', package_name = '' } = req.query;

    const pyfyzz_cmd = `pyfyzz github_pull_request -p ${package_name} -r ${record_id}`;
    console.log("Executing: ", pyfyzz_cmd);

    try {
        if (record_id && package_name) {
            // Log the full command for debugging


            // Spawn the pyfyzz process to scan the package
            const pyfyzz = spawn('pyfyzz', ['github_pull_request', '-p', package_name, '-r', record_id]);

            let output = '';
            let errorOutput = '';

            // Capture the stdout data from pyfyzz
            pyfyzz.stdout.on('data', (data) => {
                output += data.toString(); // Accumulate output
            });

            // Capture any stderr data from pyfyzz
            pyfyzz.stderr.on('data', (data) => {
                errorOutput += data.toString(); // Accumulate error output
            });

            // Handle any errors in the spawn process
            pyfyzz.on('error', (error) => {
                console.error(`Error executing pyfyzz: ${error}`);
                res.status(500).render('pages/pr_results', {
                    title: 'results',
                    pyfyzz_cmd: pyfyzz_cmd,
                    messageType: 'danger',
                    messageContent: `Error executing pyfyzz: ${error.message}`
                });
            });

            // When pyfyzz process finishes, handle the response
            pyfyzz.on('close', (code) => {
                console.log(`Process exited with code ${code}`);

                // Determine the message type and content based on the process exit code
                let messageType = code === 0 ? 'success' : 'danger';
                // let messageContent = messageType === 'success' ? output : errorOutput;
                
                // Echo back the CLI results in a Bootstrap message
                res.render('pages/pr_results', {
                    title: 'Pull Request Results',
                    pyfyzz_cmd: pyfyzz_cmd,
                    messageType: messageType,
                    messageContent: errorOutput
                });
            });

        } else {
            // If record_id or package_name is missing, show an error
            res.status(400).render('pages/pr_results', {
                title: 'Pull Request Results',
                pyfyzz_cmd: pyfyzz_cmd,
                messageType: 'danger',
                messageContent: 'record_id or package_name was not provided.'
            });
        }

    } catch (error) {
        console.error('Error:', error);
        res.status(500).render('pages/500', { title: 'Server Error' });
    }
});

module.exports = router;
