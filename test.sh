#!/bin/bash
PROFILER_HOME=/home/abyrd/otpprofiler
# CHECKOUT=`mktemp -d $PROFILER_HOME/git/XXXXXX`
CHECKOUT=$PROFILER_HOME/git/OpenTripPlanner
# git clone https://github.com/openplans/OpenTripPlanner $CHECKOUT
cd $CHECKOUT
git pull
git clean -df
#git checkout sha1
# rm ~/.m2/repository/org/opentripplanner

mvn build-helper:remove-project-artifact

mvn clean
if [ $? -eq 0 ]
then
  echo "Maven clean OK."
else
  echo "Maven clean failed."
  exit 1
fi

mvn package -DskipTests
if [ $? -eq 0 ]
then
  echo "Maven build OK."
else
  echo "Maven build failed."
  exit 2
fi

java -jar $CHECKOUT/otp-core/target/otp.jar -Xmx6G -g $PROFILER_HOME --build
if [ $? -eq 0 ]
then
  echo "Graph build OK."
else
  echo "Graph build failed."
  exit 3
fi

java -jar $CHECKOUT/otp-core/target/otp.jar -Xmx6G -g $PROFILER_HOME --server

# now poll until server is started

#sudo cp git/OpenTripPlanner/opentripplanner-api-webapp/target/opentripplanner-api-webapp.war /var/lib/tomcat6/webapps/
#sudo cp git/OpenTripPlanner/opentripplanner-webapp/target/opentripplanner-webapp.war /var/lib/tomcat6/webapps/
# restart will cause the webapps to be unpackaged and restarted
#sudo service tomcat6 restart

exit 0

