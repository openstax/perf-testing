# tutor-server performance testing

## Installation

Install python3, activate your virtualenv, then install required packages:
```sh
pip install -r requirements.txt
```

## Configuration

Setup the demo user password:
```sh
echo 'export DEMO_USER_PASSWORD=password here' > .env
```

## For old scripts

How to create a demo export:
```sh
bin/rails c
```

```rb
Demo::Export.call name: 'some_name', courses: CourseProfile::Models::Course.find(id_here)
```
