# Talky

## Setup

```bash
# Build the docker image
docker build -t talky-image .

# Modify talky/default_config.py as appropriate

# Create the database
docker run -i -t --rm -v $PWD:/lhcb-talky/ talky-image bash -c 'PYTHONPATH=/lhcb-talky/ python -m talky --production'
```

## Running a production instance of talky

```bash
docker run -i -t --rm -p 8080:80 -v $PWD:/lhcb-talky/ talky-image
```

## Running the tests

```bash
./run_tests.py
```
