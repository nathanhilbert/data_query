var map, boxLayer, drawControls, wkt;



$(document).ready(function() {





    var processBox = function(feature){
        boxLayer.removeAllFeatures();
        boxLayer.addFeatures([feature]);
        var geomclone = feature.geometry.clone();
        geomclone.transform(map.projection, "EPSG:4326")
        var wktstring = geomclone.toString();
        $("#query_wkt").val(wktstring);
    }

    var processDataRequest = function(){
        var paramstring = $("#downloadform").serialize();

      $.fileDownload('/data/ajax/downloadfiles', {
              preparingMessageHtml: "Preparing Files.  This may take a while",
              failMessageHtml: "There was a problem generating your report, please try again.",
              httpMethod: "POST",
              data: paramstring
          });
        return false;
    }


    map = new OpenLayers.Map({
        div: "map",
        wrapDateLine: true,
        projection: "EPSG:900913",
        layers: [
            new OpenLayers.Layer.OSM()
        ]
    });



    boxLayer = new OpenLayers.Layer.Vector("Box layer"); //, {projection: "EPSG:4326"}




    map.addLayers([boxLayer]);


        drawControls = new OpenLayers.Control.DrawFeature(boxLayer,
                                OpenLayers.Handler.RegularPolygon, {
                                    featureAdded: processBox,
                                    handlerOptions: {
                                        sides: 4,
                                        irregular: true
                                    }
                                }
                            );
        map.addControl(drawControls);
        
        wkt = new OpenLayers.Format.WKT();

      


    /*

    Start UI

    */




    $("#drawbox").change(function(){
        if ($(this).is(':checked')){
            drawControls.activate();
        }
        else{
            drawControls.deactivate();
        }
    });

    var processXML = function(){
        $.getJSON($(this).attr('href'), 
            function(data){
                LoadXMLString("xmldialog",data)
                $( ".xmldialog" ).dialog({width:800, height:800});
                
            });

        return false;
    }

    $("#dataform").submit(function(ev){
        if ($("#query_wkt").val() == ""){
            $("#warningtext").html("Please draw a query box first");
            return false;
        }
        params = $( this ).serialize();
        $.getJSON( "/data/ajax/queryresults", params,
            function( data ) {
                $("#bottom-table").html(data);
                $("#downloadform").submit(processDataRequest);
                $(".xmllink").click(processXML);
        });

        return false;
    });





      map.setCenter(0,0,3);
map.zoomIn();
map.zoomOut();



});