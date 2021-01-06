How to create a demo export:
bin/rails c

Demo::Export.call name: 'some_name', courses: CourseProfile::Models::Course.find(id_here)
