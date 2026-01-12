const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });
const express = require('express');
const cors = require('cors');
const RouterOSAPI = require('node-routeros-v2').RouterOSAPI;

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Mikrotik connection configuration
const getMikrotikConfig = () => ({
    host: process.env.MIKROTIK_HOST || '192.168.88.1',
    port: parseInt(process.env.MIKROTIK_PORT) || 8728,
    user: process.env.MIKROTIK_USERNAME || 'admin',
    password: process.env.MIKROTIK_PASSWORD || '',
    timeout: parseInt(process.env.MIKROTIK_TIMEOUT) || 10,
    tls: process.env.MIKROTIK_USE_SSL === 'true'
});

// Connect to Mikrotik
async function connectToMikrotik() {
    const config = getMikrotikConfig();
    const conn = new RouterOSAPI({
        host: config.host,
        user: config.user,
        password: config.password,
        port: config.port,
        timeout: config.timeout,
        tls: config.tls
    });

    try {
        await conn.connect();
        console.log(`Connected to Mikrotik at ${config.host}`);
        return conn;
    } catch (error) {
        console.error('Failed to connect to Mikrotik:', error.message);
        throw error;
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Test Mikrotik connection
app.get('/api/mikrotik/test', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const identity = await conn.write('/system/identity/print');
        await conn.close();

        res.json({
            success: true,
            message: 'Successfully connected to Mikrotik',
            identity: identity
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get hotspot users
app.get('/api/mikrotik/hotspot/users', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const users = await conn.write('/ip/hotspot/user/print');
        await conn.close();

        res.json({
            success: true,
            data: users
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Add hotspot user
app.post('/api/mikrotik/hotspot/users', async (req, res) => {
    try {
        const requestBody = req.body;
        const username = requestBody.username;
        const password = requestBody.password;
        const macAddress = requestBody.mac_address;
        const profile = requestBody.profile;
        const comment = requestBody.comment;
        const limitUptime = requestBody.limit_uptime;

        if (!username || !password) {
            return res.status(400).json({
                success: false,
                error: 'Username and password are required'
            });
        }

        const conn = await connectToMikrotik();

        const params = [
            `=name=${username}`,
            `=password=${password}`
        ];

        if (macAddress) params.push(`=mac-address=${macAddress}`);
        if (profile) params.push(`=profile=${profile}`);
        if (comment) params.push(`=comment=${comment}`);
        if (limitUptime) params.push(`=limit-uptime=${limitUptime}`);

        const result = await conn.write('/ip/hotspot/user/add', params);
        await conn.close();

        res.json({
            success: true,
            message: 'User added successfully',
            data: result
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Remove hotspot user
app.delete('/api/mikrotik/hotspot/users/:username', async (req, res) => {
    try {
        const username = req.params.username;

        const conn = await connectToMikrotik();

        // Find user by name
        const users = await conn.write('/ip/hotspot/user/print', [
            `?name=${username}`
        ]);

        if (!users || users.length === 0) {
            await conn.close();
            return res.status(404).json({
                success: false,
                error: 'User not found'
            });
        }

        const userId = users[0]['.id'];
        await conn.write('/ip/hotspot/user/remove', [
            `=.id=${userId}`
        ]);
        await conn.close();

        res.json({
            success: true,
            message: 'User removed successfully'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get active hotspot sessions
app.get('/api/mikrotik/hotspot/active', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const active = await conn.write('/ip/hotspot/active/print');
        await conn.close();

        res.json({
            success: true,
            data: active
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Disconnect user session
app.delete('/api/mikrotik/hotspot/active/:id', async (req, res) => {
    try {
        const sessionId = req.params.id;

        const conn = await connectToMikrotik();
        await conn.write('/ip/hotspot/active/remove', [
            `=.id=${sessionId}`
        ]);
        await conn.close();

        res.json({
            success: true,
            message: 'User disconnected successfully'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get hotspot profiles
app.get('/api/mikrotik/hotspot/profiles', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const profiles = await conn.write('/ip/hotspot/user/profile/print');
        await conn.close();

        res.json({
            success: true,
            data: profiles
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get system resources
app.get('/api/mikrotik/system/resources', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const resources = await conn.write('/system/resource/print');
        await conn.close();

        res.json({
            success: true,
            data: resources
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Update hotspot user
app.put('/api/mikrotik/hotspot/users/:username', async (req, res) => {
    try {
        const username = req.params.username;
        const requestBody = req.body;

        const conn = await connectToMikrotik();

        // Find user by name
        const users = await conn.write('/ip/hotspot/user/print', [
            `?name=${username}`
        ]);

        if (!users || users.length === 0) {
            await conn.close();
            return res.status(404).json({
                success: false,
                error: 'User not found'
            });
        }

        const userId = users[0]['.id'];
        const params = [`=.id=${userId}`];

        if (requestBody.password) params.push(`=password=${requestBody.password}`);
        if (requestBody.mac_address !== undefined) params.push(`=mac-address=${requestBody.mac_address}`);
        if (requestBody.profile) params.push(`=profile=${requestBody.profile}`);
        if (requestBody.comment !== undefined) params.push(`=comment=${requestBody.comment}`);
        if (requestBody.limit_uptime !== undefined) params.push(`=limit-uptime=${requestBody.limit_uptime}`);
        if (requestBody.disabled !== undefined) {
            const disabledValue = requestBody.disabled ? 'yes' : 'no';
            params.push(`=disabled=${disabledValue}`);
        }

        await conn.write('/ip/hotspot/user/set', params);
        await conn.close();

        res.json({
            success: true,
            message: 'User updated successfully'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ============================================================================
// DNS STATIC ENTRIES - For site blocking functionality
// ============================================================================

// Get all DNS static entries
app.get('/api/mikrotik/dns/static', async (req, res) => {
    try {
        const conn = await connectToMikrotik();
        const entries = await conn.write('/ip/dns/static/print');
        await conn.close();

        res.json({
            success: true,
            data: entries
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Add DNS static entry (for blocking a domain)
app.post('/api/mikrotik/dns/static', async (req, res) => {
    try {
        const { name, address, regexp, comment, disabled, ttl } = req.body;

        if (!name && !regexp) {
            return res.status(400).json({
                success: false,
                error: 'Either name or regexp is required'
            });
        }

        const conn = await connectToMikrotik();

        const params = [];

        if (name) params.push(`=name=${name}`);
        if (regexp) params.push(`=regexp=${regexp}`);
        if (address) params.push(`=address=${address}`);
        if (comment) params.push(`=comment=${comment}`);
        if (ttl) params.push(`=ttl=${ttl}`);
        if (disabled !== undefined) {
            params.push(`=disabled=${disabled ? 'yes' : 'no'}`);
        }

        const result = await conn.write('/ip/dns/static/add', params);
        await conn.close();

        // Extract the ID from the result
        const entryId = result && result.length > 0 ? result[0].ret : null;

        res.json({
            success: true,
            message: 'DNS entry added successfully',
            data: { id: entryId }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Update DNS static entry
app.put('/api/mikrotik/dns/static/:id', async (req, res) => {
    try {
        const entryId = req.params.id;
        const { name, address, regexp, comment, disabled, ttl } = req.body;

        const conn = await connectToMikrotik();

        const params = [`=.id=${entryId}`];

        if (name !== undefined) params.push(`=name=${name}`);
        if (regexp !== undefined) params.push(`=regexp=${regexp}`);
        if (address !== undefined) params.push(`=address=${address}`);
        if (comment !== undefined) params.push(`=comment=${comment}`);
        if (ttl !== undefined) params.push(`=ttl=${ttl}`);
        if (disabled !== undefined) {
            params.push(`=disabled=${disabled ? 'yes' : 'no'}`);
        }

        await conn.write('/ip/dns/static/set', params);
        await conn.close();

        res.json({
            success: true,
            message: 'DNS entry updated successfully'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Delete DNS static entry
app.delete('/api/mikrotik/dns/static/:id', async (req, res) => {
    try {
        const entryId = req.params.id;

        const conn = await connectToMikrotik();
        await conn.write('/ip/dns/static/remove', [
            `=.id=${entryId}`
        ]);
        await conn.close();

        res.json({
            success: true,
            message: 'DNS entry removed successfully'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Find DNS static entry by name or comment
app.get('/api/mikrotik/dns/static/find', async (req, res) => {
    try {
        const { name, comment } = req.query;

        const conn = await connectToMikrotik();

        let entries;
        if (name) {
            entries = await conn.write('/ip/dns/static/print', [
                `?name=${name}`
            ]);
        } else if (comment) {
            entries = await conn.write('/ip/dns/static/print', [
                `?comment=${comment}`
            ]);
        } else {
            entries = await conn.write('/ip/dns/static/print');
        }

        await conn.close();

        res.json({
            success: true,
            data: entries
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(500).json({
        success: false,
        error: err.message || 'Internal server error'
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Mikrotik Agent running on port ${PORT}`);
    console.log(`Mikrotik host: ${getMikrotikConfig().host}`);
});
