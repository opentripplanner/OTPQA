#!/bin/bash
PROFILER_HOME=/home/abyrd/otpprofiler
#CHECKOUT=`mktemp -d $PROFILER_HOME/git/XXXXXX`
CHECKOUT=$PROFILER_HOME/git/OpenTripPlanner
#git clone https://github.com/openplans/OpenTripPlanner $CHECKOUT
cd $CHECKOUT
git pull
git clean -df
#git checkout sha1
# rm ~/.m2/repository/org/opentripplanner
mvn build-helper:remove-project-artifact
echo "Maven build status $?"
#mvn clean verify
mvn package -DskipTests
if [ $? -eq 0 ]
then
  echo "ok"
else
  echo "Maven build failed"
fi
java -cp $CHECKOUT/opentripplanner-graph-builder/target/graph-builder.jar \
     -Xmx6G \
     org.opentripplanner.graph_builder.GraphBuilderMain \
     /var/otp/graphs/pdx_baseline/graph-builder.xml

#sudo cp git/OpenTripPlanner/opentripplanner-api-webapp/target/opentripplanner-api-webapp.war /var/lib/tomcat6/webapps/
#sudo cp git/OpenTripPlanner/opentripplanner-api-webapp/target/opentripplanner-webapp.war /var/lib/tomcat6/webapps/
# restart will cause the webapps to be unpackaged and restarted
#sudo service tomcat6 restart

exit 0

