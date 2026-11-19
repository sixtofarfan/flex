
odoo.define('website.user_custom_map', function (require) {
    'use strict';
    require('web.dom_ready');

    mapboxgl.accessToken = 'pk.eyJ1IjoiZ3JlZ29yaW9jb2RlIiwiYSI6ImNrNHQwbHB6czFvcTMzbHQyN296b3J6YnIifQ.Za4wCJReEIi2wJ3OPTBTjQ';
    var a = document.querySelector("#lng");
    var b = document.querySelector("#lat");
    var map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v9',
        center: [a.value, b.value],
        zoom: 10
    });
    var temp = 20;
    var geocoder = new MapboxGeocoder({
        accessToken: mapboxgl.accessToken,
        language: 'de-DE',
        mapboxgl: mapboxgl
    });
    map.addControl(geocoder);

    var geoloca = function (lng, lat) {
        let a = document.querySelector("#lng");
        let b = document.querySelector("#lat");
        a.value = lng;
        b.value = lat;
    }
    map.on('load', function () {
        var width = 20; // The image will be 64 pixels square
        var bytesPerPixel = 4; // Each pixel is represented by 4 bytes: red, green, blue, and alpha.
        var data = new Uint8Array(width * width * bytesPerPixel);
        let a = document.querySelector("#lng");
        let b = document.querySelector("#lat");
        if (a.value == 0 & b.value == 0) {
            geoloca(-76.91042, -12.04688);
        } else {
            geoloca(a.value, b.value);
        }


        for (var x = 0; x < width; x++) {
            for (var y = 0; y < width; y++) {
                var offset = (y * width + x) * bytesPerPixel;
                data[offset + 0] = (y / width) * 255; // red
                data[offset + 1] = (x / width) * 255; // green
                data[offset + 2] = 128; // blue
                data[offset + 3] = 255; // alpha
            }
        }

        map.addImage('gradient', { width: width, height: width, data: data });

        map.addLayer({
            'id': temp.toString(),
            'type': 'symbol',
            'source': {
                'type': 'geojson',
                'data': {
                    'type': 'FeatureCollection',
                    'features': [
                        {
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [a.value, b.value]
                            }
                        }
                    ]
                }
            },
            'layout': {
                'icon-image': 'gradient'
            }
        });
    });
    map.on('dragend', function () {
        var LntLog = map.getCenter()
        if (map.getLayer(temp.toString())) {
            map.removeLayer(temp.toString())
        }
        geoloca(LntLog.lng, LntLog.lat);
        var cor = [LntLog.lng, LntLog.lat]
        temp++;
        map.addLayer({
            'id': temp.toString(),
            'type': 'symbol',
            'source': {
                'type': 'geojson',
                'data': {
                    'type': 'FeatureCollection',
                    'features': [
                        {
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Point',
                                'coordinates': cor
                            }
                        }
                    ]
                }
            },
            'layout': {
                'icon-image': 'gradient'
            }
        });
    });
});