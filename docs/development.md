<!--
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Development

This guide covers development setup and contributing to otava-test-data.

## Development Setup

Clone the repository and install development dependencies:

```bash
git clone https://github.com/your-username/otava-test-data.git
cd otava-test-data
pip install -e ".[all]"
```

## Running Tests

Run the test suite with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=otava_test_data --cov-report=html
```

## Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
ruff check .
ruff format .
```

## Building Documentation

Build the Sphinx documentation:

```bash
cd docs
make html
```

Or using invoke:

```bash
invoke docs
```

## Releasing

Releases are automated via GitHub Actions. The workflow publishes to PyPI when a release is created.

### Release Process

1. Update the version in `pyproject.toml`
2. Commit the version change
3. Create and push a git tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Create a GitHub Release from the tag
5. The GitHub Action will automatically build and publish to PyPI

### PyPI Trusted Publishing Setup

The publish workflow uses PyPI trusted publishing (OIDC). To enable this:

1. Go to your PyPI project settings
2. Add a new trusted publisher with:
   - Owner: your GitHub username or organization
   - Repository: otava-test-data
   - Workflow name: publish.yml
   - Environment: pypi

For TestPyPI, create a similar trusted publisher with environment: testpypi

### Manual Testing with TestPyPI

You can manually trigger the workflow to publish to TestPyPI for testing:

1. Go to Actions > Publish to PyPI
2. Click "Run workflow"
3. This will build and publish to TestPyPI only

Install from TestPyPI to verify:

```bash
pip install --index-url https://test.pypi.org/simple/ otava-test-data
```
