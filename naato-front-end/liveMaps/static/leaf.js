//url, making post calls to DS to retrieve on time arrival status
var url = "https://b3q2wc6cgggny2vutpm32q5q7a.apigateway.us-ashburn-1.oci.customer-oci.com/function/predict"

//Fetch Headers
var newHeaders = new Headers();
newHeaders.append('Content-Type', 'application/json');
newHeaders.append('Accept', 'application/json');


//Set Austin coordinates
var mymap = L.map('mapid').setView([30.2672, -97.7431], 10);
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' + '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' + 'Imagery ÃÂÃÂ© <a href="https://www.mapbox.com/">Mapbox</a>',
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1
}).addTo(mymap);

//Package Metrics (ID, coordinates, status, dest...)
var packageTableData = [];
//running_list = [package1, package2, package3, package4]
var running_list = [];
//running_dict = { package_id1 : [marker1_4], package_id2 : [marker2_1, marker2_2]}
var running_dict = {};
//Boolean value set when marker clicked
var isClicked='TRUE';
//packageTracker->Save latest package Information
var packageTracker=[];
//Table Package Unique Identifier
var idList=[];
//ID unique identifier starts at one
var id=1;
//Tabulator Row Selection
var selectedTablePackage;



//Storing latest package coordinatescoordinates
var latArray={};
var lonArray={};
var degrees=0;

var packageTableDataOrigin=[{
  id:id,
  package_id: 'N/A',
  latitude: 'N/A',
  longitude: 'N/A',
  transit_time: 'N/A',
  status: 'N/A',
  prediction: 'N/A'
}]

//initialize table
var table = new Tabulator("#package-table", {
  layout:'fitData',
  data: packageTableDataOrigin, //assign data to table
  selectable:true,
  pagination:"local",
  paginationSize:5,
  columns:[
    {title:"ID", field:"id",headerSort:false},
    {title:"Package ID", field:"package_id",headerSort:false},
    {title:"Latitude", field:"latitude",headerSort:false},
    {title:"Longitude", field:"longitude",headerSort:false},
    {title:"Transit Time", field:"transit_time",headerSort:false},
    {title:"Status", field:"status",headerSort:false},
    {title:"Package Arrival", field:"prediction",headerSort:false}
  ],

  rowClick:function(e, row){
    //e - the click event object
    //row - row component

    var selectedData = table.getSelectedData(); //get array of currently selected row components.
    selectedTablePackage=selectedData[0].package_id;

    row.toggleSelect(); //toggle row selected state on row click
  }
  
});


table.hideColumn('id');



//Stream events happen here
var source = new EventSource('/stream'); //ENTER YOUR TOPICNAME HERE
source.addEventListener('message', function(e) {

    //Define package object
    obj = JSON.parse(e.data);


    //Seconds to minutes
    var transitInMinutes = Math.floor(obj.TRANSIT_TIME / 60);


    //Latest package information sent to Data Science for on-time prediction 
    var query = {
        "input": [
            [obj.LATITUDE, obj.LONGITUDE, obj.TRANSIT_TIME]
        ]
    };


    //Delivery Truck icon
    var packageDelivery = L.icon({
      iconUrl: '../static/top-view.png',
      iconSize: [20, 20], // size of the icon
  
    });
    //Push coordinates to model
    pushCoordinates(url);

    function pushCoordinates(url) {
        fetch(url, {
                mode: 'cors',
                method: 'POST',
                headers: newHeaders,
                body: JSON.stringify(query),

            })
            .then(response => response.json()) //converts response data to JSON
            .then(data => {



                if (obj.STATUS == 0) {
                    obj.STATUS = "In progress";
                } else if (obj.STATUS == 1) {
                    obj.STATUS = "Delivered";
                } else {
                    obj.STATUS = "N/A";
                }

                if (packageTableDataOrigin[0].package_id == 'N/A') {

                  //Defining first table row
                  packageTableData[0] = {
                    id:1,
                    package_id: obj.PACKAGE_ID,
                    latitude: obj.LATITUDE,
                    longitude: obj.LONGITUDE,
                    transit_time: transitInMinutes + ' min',
                    status: obj.STATUS,
                    prediction: data.prediction
                  }

                  //Add to array of packages
                  packageTableData.push({
                    package_id: obj.PACKAGE_ID,
                    latitude: obj.LATITUDE,
                    longitude: obj.LONGITUDE,
                    transit_time: transitInMinutes + ' min',
                    status: obj.STATUS,
                    prediction: data.prediction

                  })

                  //Store ID value here
                  idList.push({package_id:obj.PACKAGE_ID, id:id})

                  //Increment ID
                  id++;
                  
                  //Break if case-N/A with clear
                  packageTableDataOrigin[0].package_id='Clear';

                  //Update first row w/ new package
                  table.updateRow(1,packageTableData[0])
                }

                //if package doesn't exist, append package to table
                if (packageTableData.every(tableData => tableData.package_id !== obj.PACKAGE_ID)) {

                    //Add data to table

                    table.addData([{
                      id: id,
                      package_id: obj.PACKAGE_ID,
                      latitude: obj.LATITUDE,
                      longitude: obj.LONGITUDE,
                      transit_time: transitInMinutes + ' min',
                      status: obj.STATUS,
                      prediction: data.prediction
                    }])

                  
                    //Push to array

                    packageTableData.push({
                      package_id: obj.PACKAGE_ID,
                      latitude: obj.LATITUDE,
                      longitude: obj.LONGITUDE,
                      transit_time: transitInMinutes + ' min',
                      status: obj.STATUS,
                      prediction: data.prediction
                    })


                    //Keep populating table and updating id information
                    idList.push({package_id:obj.PACKAGE_ID, id:id})
                    id++


                } else {

                    //Find package ID in array
                    var packageIDIndex = packageTableData.findIndex(index => index.package_id === obj.PACKAGE_ID);
                    //Along with key
                    var packageKey=idList.filter(id=>id.package_id==obj.PACKAGE_ID)


                    //Overwrite existing package data with latest stream information
                    packageTableData[packageIDIndex] = {
                        id:packageKey[0].id,
                        package_id: obj.PACKAGE_ID,
                        latitude: obj.LATITUDE,
                        longitude: obj.LONGITUDE,
                        transit_time: transitInMinutes + ' min',
                        status: obj.STATUS,
                        prediction: data.prediction
                    }
                    //Overwrite Row
                    table.updateRow(packageKey[0].id,packageTableData[packageIDIndex])
                }

                //Push new packages to running list of packages in stream
                if (!running_list.includes(obj.PACKAGE_ID)) {
                    //Pushes package_ID only
                    running_list.push(obj.PACKAGE_ID)
                    //Running dict has no markers yet
                    running_dict[obj.PACKAGE_ID] = []
                    //Save coordinates-Same as running dict
                    latArray[obj.PACKAGE_ID] = []
                    lonArray[obj.PACKAGE_ID] = []
                    //Track new packages only
                    packageTracker.push({packageID:obj.PACKAGE_ID, latitude: obj.LATITUDE, longitude: obj.LONGITUDE, status:obj.STATUS, prediction:data.prediction,  packageClicked:'FALSE'});
                }

                //Re-initialize marker after coordinate updates
                if (running_list.includes(obj.PACKAGE_ID)) {

                    //Current package being tracked
                    var packageTracked=packageTracker.filter(track=>track.packageID==obj.PACKAGE_ID)

                    //Pushing latest lats and lons
                    latArray[packageTracked[0].packageID].push(obj.LATITUDE)
                    lonArray[packageTracked[0].packageID].push(obj.LONGITUDE)


                    //Update coordinates
                    if(latArray[packageTracked[0].packageID].length>1){

                      //Opposite side
                      var opposite=lonArray[packageTracked[0].packageID][lonArray[packageTracked[0].packageID].length-1] - lonArray[packageTracked[0].packageID][lonArray[packageTracked[0].packageID].length-2];
                      //Adjacent side
                      var adjacent=latArray[packageTracked[0].packageID][latArray[packageTracked[0].packageID].length-1] - latArray[packageTracked[0].packageID][latArray[packageTracked[0].packageID].length-2];                     
                      var arcTangent=Math.atan2(opposite,adjacent);
                      var pi = Math.PI;
                      degrees = ((arcTangent * (180/pi))-90);

                    }

                    console.log(degrees)

                    //Remove last marker
                    for (var i = 0; i < running_dict[obj.PACKAGE_ID].length; i++) {
                        mymap.removeLayer(running_dict[packageTracked[0].packageID][i]);
                    };

                    //Create new marker
                    newMarker = L.marker([obj.LATITUDE, obj.LONGITUDE], {rotationAngle: degrees, rotationOrigin: 'center center', icon:packageDelivery}).addTo(mymap);
                    running_dict[packageTracked[0].packageID].push(newMarker);

                    if(selectedTablePackage == packageTracked[0].packageID){


                      if(packageTracked[0].packageClicked=='FALSE'){
                        packageTracked[0].packageClicked='TRUE';
                      }else{
                        packageTracked[0].packageClicked='FALSE';
                      }

                      selectedTablePackage='Clear';

                    }

                    //Click on marker
                    newMarker.on('click',function(){
                          if(packageTracked[0].packageClicked=='FALSE'){
                            packageTracked[0].packageClicked='TRUE';
                          }else{
                            packageTracked[0].packageClicked='FALSE';
                          }
                        })





                        if(packageTracked[0].packageClicked=='FALSE'){

                          newMarker.bindPopup('Package ID: ' + packageTracked[0].packageID + "<br>" +
                          'Status: ' + packageTracked[0].status + "<br>" +
                          'Prediction: ' + packageTracked[0].prediction,{autoClose:false }
                          ).closePopup();

                        }else{
                          newMarker.bindPopup('Package ID: ' + packageTracked[0].packageID + "<br>" +
                          'Status: ' + packageTracked[0].status + "<br>" +
                          'Prediction: ' + packageTracked[0].prediction,{autoClose:false }
                          ).openPopup();
                        }
                }

            });
    }

}, false)

