const express = require('express');
const cors = require('cors');
require('./db');
const authRoutes = require('./routes/auth');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => res.json({ ok: true, ts: Date.now() }));
app.use('/api/auth', authRoutes);
app.use('/api/assets', require('./routes/assets'));

app.use((req, res) => res.status(404).json({ error: 'not_found' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`[server] http://localhost:${PORT}`));
