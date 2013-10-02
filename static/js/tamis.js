var map, vectorLayer, tamislayer, grantslayer;

google.load("visualization", "1", {packages:["corechart"]});

$(document).ready(function() {


    tamisstyle = new OpenLayers.Style(
            {
                //pointRadius: "${calculateRadius}",
                pointRadius: 7,
                strokeColor: "${gender}",
                fillColor: "${gender}",
                graphicName: 'square',
                fillOpacity: .5,
                strokeOpacity: .7,
            }
    );

    tsm = new OpenLayers.StyleMap({
        "default": tamisstyle,
        "select": tamisstyle
    });




    tamislayer = new OpenLayers.Layer.Vector("Tamis Layer", {
                styleMap: tsm,
                projection: new OpenLayers.Projection("EPSG:4326"),
                strategies: [new OpenLayers.Strategy.Fixed()],
                protocol: new OpenLayers.Protocol.HTTP({
                    url: "/myfirstapp/ajax/gettamis",
                    format: new OpenLayers.Format.GeoJSON(),
                    params: {"service": "MEC", "tamisservices": "Crafts,Entertainment,Guides,Hotels,Restaurants,Tours"}
                }),
                eventListeners: {
                    //"featuresadded": function() {
                    //    this.map.zoomToExtent(this.getDataExtent());
                    //}
                }
            });

    grantsstyle = new OpenLayers.Style(
            {
                //pointRadius: "${calculateRadius}",
                pointRadius: "${amount}",
                strokeColor: "#b2b200",
                fillColor: "#b2b200",
                graphicName: 'circle',
                fillOpacity: .3,
                strokeOpacity: .3,
            }
    );

    grantssm = new OpenLayers.StyleMap({
        "default": grantsstyle,
        "select": grantsstyle
    });




    grantslayer = new OpenLayers.Layer.Vector("Grants Layer", {
                styleMap: grantssm,
                projection: new OpenLayers.Projection("EPSG:4326"),
                strategies: [new OpenLayers.Strategy.Fixed()],
                protocol: new OpenLayers.Protocol.HTTP({
                    url: "/myfirstapp/ajax/getgrantdata",
                    format: new OpenLayers.Format.GeoJSON(),
                }),
                eventListeners: {
                    //"featuresadded": function() {
                    //    this.map.zoomToExtent(this.getDataExtent());
                    //}
                }
            });

    wbstyle = new OpenLayers.Style(
        OpenLayers.Util.extend(
            OpenLayers.Feature.Vector.style['default'],
            {
                strokeColor: "${projectcolor}",
                fillColor: "${projectcolor}",
                pointRadius: 6,
                graphicName: 'circle'
            }
        )
    );

    wbsm = new OpenLayers.StyleMap({
        "default": wbstyle
    });


    wblayer = new OpenLayers.Layer.Vector("World Bank Layer", {
                styleMap: wbsm,
                projection: new OpenLayers.Projection("EPSG:4326"),
                strategies: [new OpenLayers.Strategy.Fixed()],
                protocol: new OpenLayers.Protocol.HTTP({
                    url: "/myfirstapp/ajax/getworldbank",
                    format: new OpenLayers.Format.GeoJSON()
                    //url: "http://10.233.3.87/proxy.php",
                    //format: new OpenLayers.Format.GeoJSON(),
                    //params: {"url": "http://localhost:81/MEC_TAMIS.nsf/openagent", "mode":"native"}
                }),
                eventListeners: {
                    "featuresadded": function() {
                        this.map.zoomToExtent(this.getDataExtent());
                    }
                }
            });


    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 5;
    // make OL compute scale according to WMS spec
    OpenLayers.DOTS_PER_INCH = 25.4 / 0.28;

    // if this is just a coverage or a group of them, disable a few items,
    // and default to jpeg format
    format = 'image/png';

    // setup tiled layer
    tiled = new OpenLayers.Layer.WMS(
        "Project Area", "http://10.233.3.87:8080/geoserver/topp/wms",
        {
            LAYERS: 'topp:ProParque_parks_19_WGS84',
            STYLES: '',
            format: format,
            //tiled: true,
            transparent: true
            //tilesOrigin : map.maxExtent.left + ',' + map.maxExtent.bottom
        },
        {
            buffer: 0,
            displayOutsideMaxExtent: true,
            singleTile: true,
            isBaseLayer: false,
            yx : {'EPSG:4326' : true},
            visible:false
        } 
    );

    map = new OpenLayers.Map({
        div: "map",
        layers: [
            new OpenLayers.Layer.OSM()
        ]
    });
    map.addLayers([tiled, grantslayer, wblayer, tamislayer]);

    tiled.setVisibility(false);


/*

MAP CONTROLS




*/
        var onFeatureSelect = function(feature) {
            selectedFeature = feature;
            if (selectedFeature.layer.name == "Tamis Layer"){
                content = "<div style='font-size:.8em'>" + selectedFeature.attributes.name + "<br/>Sector: " + selectedFeature.attributes.sector + "</div>";
            }
            else if (selectedFeature.layer.name == "World Bank Layer"){
                //content = "<div style='font-size:.8em'>" + selectedFeature.attributes.name + "<br/>Sector: " + selectedFeature.attributes.sector + "</div>",
                content = "<div style='font-size:.8em'>" + selectedFeature.attributes.project_name + "<br/>Total Amount: $" + selectedFeature.attributes.totalamt + 
                        "<br/><a href='" + selectedFeature.attributes.url + "' target='blank'>See more info</a></div>";
            }
            else {
                content = "<div style='font-size:.8em'>" + selectedFeature.attributes.title + "<br/>Amount: $" + selectedFeature.attributes.amount * 2500 + "</div>";
            }

            popup = new OpenLayers.Popup.FramedCloud("chicken", 
                                     feature.geometry.getBounds().getCenterLonLat(),
                                     null,
                                     content,
                                     null, true);
            feature.popup = popup;
            map.addPopup(popup);
        }
        var onFeatureUnselect = function(feature) {
            map.removePopup(feature.popup);
            feature.popup.destroy();
            feature.popup = null;
        } 

        selectControl = new OpenLayers.Control.SelectFeature([tamislayer, wblayer, grantslayer],
                {onSelect: onFeatureSelect, onUnselect: onFeatureUnselect});



        map.addControl(selectControl);
        selectControl.activate();



/**


START UI





*/
    function drawCharts(thedata, chartoptions){

        //var parsestring = summary_data.replace(/&quot;/g, "\"");
        google.load("visualization", "1", {packages:["corechart"]});
        thedata.unshift(chartoptions['headers']);
        var summary_output_data = google.visualization.arrayToDataTable(thedata);
        var options = {title:chartoptions['title']};
        var chart = new google.visualization.PieChart(document.getElementById(chartoptions['target']));
        chart.draw(summary_output_data, options);

    }

    var updateTamis = function(){

    }

    var toggleLayer = function(layername, visibility){
        mylayer = map.getLayersByName(layername)[0];
        mylayer.setVisibility(visibility);
    }

    var uifunction = function(){

        $( "#accordion" ).accordion({
          collapsible: true,
          heightStyle: "content"
        });

        $('#wbform').submit(function(){

            $.ajax({
              dataType: "json",
              url: "/myfirstapp/charts/getworldbank",
              data: {},
              success: function(data){
                drawCharts(data['data'], {"title": "Project by award amount", "headers": ["Project Name", "Amount"], "target": "worldbank_projects_chart"});
                $("#worlbank_projects_total").html(data['aggregates']['totalamount'])
              }
            });
            return false;
        });

        $("#tamisform").submit(function(){
            var formobj = $(this).serializeArray();
            paramarray = [];
            for (theval in formobj){
                paramarray.push(formobj[theval]['value'])
            }
            paramstring = paramarray.join(",");
            tamislayer.protocol.params.tamisservices = paramstring;
            tamislayer.refresh({force:true});

                    //make sure you send the variables to this as well to charts and number updated
                    //http://localhost:81/HondurasProParqueTAMIS.nsf/opencharts?OpenAgent
            $.ajax({
              dataType: "json",
              url: "/myfirstapp/charts/gettamis",
              data: {tamisservices: paramstring},
              success: function(data){
                tamischartdata = data['sector_chart']
                drawCharts(tamischartdata, {"title": "Business by Sector", "headers": ["Sector", "Number"], "target": "tamis_sector_chart"});
                grantsdata = data['grants_chart'];
                drawCharts(grantsdata, {"title": "Grants by amount", "headers": ["Title", "Amount"], "target": "grants_chart"});
                gender_chart =  data['gender_chart'];
                $("#tamis_women").html(gender_chart['females']);
                $("#tamis_men").html(gender_chart['males']);
              }
            });
            return false;

        });


        $(".togglelayer").change(function(){
            toggleLayer($(this).val(), $(this).attr("checked"));
        });




        return;
    }
    uifunction();
    $("#tamisform").submit();
    $('#wbform').submit();

});