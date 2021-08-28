odoo.define('module.DianInvoice', function(require) {
    "use strict";
    var rpc = require('web.rpc');

    $(document).ready(function() {
        var flagLoaded = false;
        var mainIntervalTime = 2500;
        setInterval(function() {
            $(document).on("blur", ".div_vat input", function() {
                var ruc = $(".div_vat input").val();
                var data = { "params": { 'nit': ruc } }
                    // $.ajax({
                    //     type: "POST",
                    //     url: '/dianefact/get_nit',
                    //     data: JSON.stringify(data),
                    //     dataType: 'json',
                    //     contentType: "application/json",
                    //     async: false,
                    //     success: function(response) {
                    //         console.log(response)
                    //         if (response.result.status == "OK") {
                    //             $("input[name=name]").val(response.result.denominacion);
                    //             //$(".client-address-street").val(response.result.address);
                    //             //$(".client-address-city").val(response.result.city);
                    //             swal("La empresa es valida", "", "success");
                    //         } else {
                    //             swal(response.result.status, "", "warning");
                    //         }
                    //     }
                    // });
            })

            $(document).on("blur", "input[name='vat']", function() {
                var nit = $("input[name='vat']").val();
                var dv = calcular_DV(nit);
                $("input[name='vat_dv']").val(dv);
                $("span[name='vat_dv']").val(dv);
                var id = get_url_param('id')
                var model = get_url_param('model')
                model = model.replace(".", "_")
                var data = { "params": { "id": id, "vat_dv": dv, "model": model } }
                $.ajax({
                    type: "POST",
                    url: '/dianefact/update_vat_dv',
                    data: JSON.stringify(data),
                    dataType: 'json',
                    contentType: "application/json",
                    async: false,
                    success: function(response) {}
                });
            });
            try
            {
                if(country_id=="" || country_id==null)
                    {
                        country_id = $("select[name='country_id']").find('option[text="Colombia"]').val();
                    }
            }
            catch
            {}
                
            
            
        }, mainIntervalTime);


        $(document).on("change", "select[name='state_id']", function () {
            //if($(".pos-dianfact").length>0)
            {         
                var country_id = $("select[name='country_id']").val();
                if(country_id=="")
                {
                    country_id = $("select[name='country_id']").find('option[text="Colombia"]').val();
                }
                var state_id = $("select[name='state_id']").val();
                if(!state_id)
                    state_id = 0;
                populate_location(country_id, state_id, 0);                
            }
        }); 
        $(document).on("change", "select[name='country_id']", function () {
            //if($(".pos-dianfact").length>0)
            {         
                var country_id = $("select[name='country_id']").val();
                if(country_id==""  || country_id==null)
                {
                    country_id = $("select[name='country_id']").find('option[text="Colombia"]').val();
                }
                var state_id = $("select[name='state_id']").val();
                if(state_id=="" || state_id==null)
                    state_id = 0;
                populate_location(country_id, state_id, 0);                
            }
        }); 

        $(document).on("change", "select[name='district_id']", function () {
            var code = $(this).children("option:selected").attr("code"); 
            $("input[name='zip']").val(code);
        });
    });
})

function calcular_DV(myNit) {
    var vpri,
        x,
        y,
        z;

    // Se limpia el Nit
    myNit = myNit.replace(/\s/g, ""); // Espacios
    myNit = myNit.replace(/,/g, ""); // Comas
    myNit = myNit.replace(/\./g, ""); // Puntos
    myNit = myNit.replace(/-/g, ""); // Guiones

    // Se valida el nit
    if (isNaN(myNit)) {
        console.log("El nit/cédula '" + myNit + "' no es válido(a).");
        return "";
    };

    // Procedimiento
    vpri = new Array(16);
    z = myNit.length;

    vpri[1] = 3;
    vpri[2] = 7;
    vpri[3] = 13;
    vpri[4] = 17;
    vpri[5] = 19;
    vpri[6] = 23;
    vpri[7] = 29;
    vpri[8] = 37;
    vpri[9] = 41;
    vpri[10] = 43;
    vpri[11] = 47;
    vpri[12] = 53;
    vpri[13] = 59;
    vpri[14] = 67;
    vpri[15] = 71;

    x = 0;
    y = 0;
    for (var i = 0; i < z; i++) {
        y = (myNit.substr(i, 1));
        // console.log ( y + "x" + vpri[z-i] + ":" ) ;

        x += (y * vpri[z - i]);
        // console.log ( x ) ;    
    }

    y = x % 11;
    // console.log ( y ) ;

    return (y > 1) ? 11 - y : y;
}

function get_url_param(name) {
    url = location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?#&]' + name + '(=([^&#]*)|&|#|$)'),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
    var captured = /id=([^&]+)/.exec(url)[1]; // Value is in [1] ('384' in our case)
    var result = captured ? captured : 'myDefaultValue';
}

function populate_location(country_id, state_id,district_id) {
    const capitalize = (s) => {
        if (typeof s !== 'string') return ''
        return s.charAt(0).toUpperCase() + s.slice(1)
    }
    var data = { "params": { "country_id": country_id, "state_id": state_id, "district_id": district_id } }
    $.ajax({
        type: "POST",
        url: '/dianefact/populate_location',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function (response) {
            if (response.result.country_id > 0) {
                var country_options = "<option value='0'>seleccionar</option>";
                var state_options = "<option value='0'>seleccionar</option>";
                var province_options = "<option value='0'>seleccionar</option>";
                var district_options = "<option value='0'>seleccionar</option>";
                if (response.result.states) {

                    try {
                        var countries = response.result.countries
                        countries.forEach(function (country, index) {
                            country_options += "<option value='" + country.id + "' code='" + country.code + "'>" + capitalize(String(country.name)) + "</option>";
                        });
                        $("select[name='country_id']").html("");
                        $("select[name='country_id']").append(country_options);
                        $("select[name='country_id']").val(response.result.country_id);
                    }
                    catch (error) {
                    }

                    try {
                        var states = response.result.states;
                        states.forEach(function (state, index) {
                            state_options += "<option value='" + state.id + "' code='" + state.code + "'>" + capitalize(String(state.name)) + "</option>";
                        });
                        $("select[name='state_id']").html("");
                        $("select[name='state_id']").append(state_options);
                    }
                    catch (error) {
                    }


                    try {
                        var districts = response.result.districts
                        districts.forEach(function (district, index) {
                            district_options += "<option value='" + district.id + "' code='" + district.code + "'>" + capitalize(String(district.name)) + "</option>";
                        });

                        $("select[name='district_id']").html("");
                        $("select[name='district_id']").append(district_options);

                    }
                    catch (error) {
                    }

                }
                $("select[name='state_id']").val(state_id)
                $("select[name='district_id']").val(district_id)
            }
        }
    });
}