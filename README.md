<div align="center">
    <img alt="" src="document/logo.png" height="128">
    <h1>Sightrack</h1>
    <p>Inference of where people are looking from 360-degree video</p>
    <p><b> ⚠️ This project is under development for research. It will release as OSS is WIP! ⚠️ </b></p>
</div>

<p align="center">
    <img alt="" src="https://img.shields.io/badge/LICENSE-WTFPL-blueviolet?style=for-the-badge&labelColor=black&link=.%2FLICENSE">
    <img alt="" src="https://img.shields.io/badge/PYTHON-3.9.*-orange?style=for-the-badge&logo=python&labelColor=black&link=.%2FLICENSE">
    <img alt="" src="https://img.shields.io/badge/NODEJS-18.*-green?style=for-the-badge&logo=node.js&labelColor=black&link=.%2FLICENSE">
</p>

# ⚡ Quick Start

## Requirements

- Python 3.9 ([Python install guide](./document/guides/install-python.md))
- Node.js 18 ([Node.js install guide](./document/guides/install-nodejs.md))

## Setup

Every time you run `npm install`, a Python virtual environment is automatically created (if it does not exist) under
./backend and the necessary packages are installed.

```bash
git clone https://github.com/kerthical/sightrack.git
cd sightrack
npm install
```

## Run

### Web Interface

Running `npm start` will build the frontend package and output it to ./frontend/dist. Then the backend package's
src/server.py is executed. Visit https://127.0.0.1:8080 to view the web interface.

```bash
npm start
```

### CLI

```bash
npm run cli -- [args]
```