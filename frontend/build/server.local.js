'use strict'
const fs = require('fs')
const path = require('path')
const express = require('express')
const webpack = require('webpack')
const webpackConfig = require('./webpack.local')
const config = require('./config')

const app = express()

// Use port 3000 for local development to avoid conflicts
const port = 3000
webpackConfig.entry.client = [
  `webpack-hot-middleware/client?reload=true`,
  webpackConfig.entry.client
]

let compiler

try {
  compiler = webpack(webpackConfig)
} catch (err) {
  console.error(err.message)
  process.exit(1)
}

const devMiddleWare = require('webpack-dev-middleware')(compiler, {
  publicPath: webpackConfig.output.publicPath,
  quiet: true
})

app.use(devMiddleWare)
app.use(require('webpack-hot-middleware')(compiler, {
  log: () => {}
}))

// Serve static files from the static directory
app.use(express.static(path.join(__dirname, '../static')))

const mfs = devMiddleWare.fileSystem
const file = path.join(webpackConfig.output.path, 'index.html')

devMiddleWare.waitUntilValid()

// Allow connections from any host for Docker development
app.get('*', (req, res) => {
  devMiddleWare.waitUntilValid(() => {
    const html = mfs.readFileSync(file)
    res.end(html)
  })
})

console.log(`Frontend development server starting on port ${port}`)
console.log(`Backend API URL: ${process.env.BACKEND_URL || 'http://localhost:8000'}`)

app.listen(port, '0.0.0.0', () => {
  console.log(`Frontend ready at http://localhost:${port}`)
})