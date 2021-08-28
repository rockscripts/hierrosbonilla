odoo.define('module.DianInvoice', function(require) {
    "use strict";
    var rpc = require('web.rpc');

    $(document).ready(function() {
        var flagLoaded = false;
        var mainIntervalTime = 2500;
        var index_Exc = 0;

        var locationInterval = setInterval(function() 
        {
            if($(".new-customer").length>0)
            {
                $(document).on("click", ".new-customer", function () {
                    if($(".pos-dianfact").length>0)
                    {                
                        var country_id = $("select[name='country_id']").val();
                        if(!country_id)
                        country_id = 0;
                        populate_location(country_id, 0, 0);                
                    }
                }); 
                $(document).on("change", "select[name='state_id']", function () {
                    if($(".pos-dianfact").length>0)
                    {         
                        var country_id = $("select[name='country_id']").val();
                        var state_id = $("select[name='state_id']").val();
                        if(!state_id)
                            state_id = 0;
                        populate_location(country_id, state_id, 0);                
                    }
                }); 
                $(document).on("change", "select[name='district_id']", function () {
                    if($(".pos-dianfact").length>0)
                    {         
                        var code = $(this).children("option:selected").attr("code");             
                        $("input[name='zip']").val(code)
                    }
                }); 
    
                $(document).on("change", "input[name='vat']", function () {
                    if($(".pos-dianfact").length>0)
                    {         
                        var vat = $(this).val();   
                        var dv = calcular_DV(vat);          
                        $("input[name='vat_dv']").val(dv)
                    }
                }); 
                $(document).on("click", ".client-details div.edit", function () {               
                    if($(".pos-dianfact").length>0)
                    {  
                        var partner_id = $("input[name='partner_id']").val();
                        if(partner_id>0)      
                        {
                        var data = { "params": { 'partner_id': partner_id} }
                                //console.log(data)
                            $.ajax({
                                type: "POST",
                                url: '/dianefact/get_partner',
                                data: JSON.stringify(data),
                                dataType: 'json',
                                contentType: "application/json",
                                async: false,
                                success: function(response) {
                                    if (response.result) {
                                        var partner = response.result;
                                        console.log (partner)
                                        populate_location(partner.country_id, partner.state_id,partner.district_id);                                    
                                        $("input[name='zip']").val(partner.zip);
                                        $("input[name='country_id']").val(partner.country_id);
                                        $("input[name='state_id']").val(partner.state_id);
                                        $("input[name='district_id']").val(partner.district_id);
                                        $("input[name='street']").val(partner.street);
                                        $("#dian_tipo_documento").val(response.result.dian_tipo_documento)
                                    }
                                }
                            }); 
                        }
                        
                    }
                });
                clearInterval(locationInterval);
            }
            
        }, 5);

        setInterval(function() {
            if ($("input[name='reference']").length > 0) {
                $("input[name='reference']").attr("placeholder","Usar en circular al registrar pago");
            }
            if ($("span[name='dian_request_status']").length > 0) {
                var dian_request_status = $("span[name='dian_request_status']").text();
                displayRequestStatus1(dian_request_status);
            }
            // Display requst status            
            if ($("span[name='dian_request_status']").length > 0) {
                var dian_request_status = $("span[name='dian_request_status']").text();
                displayRequestStatus1(dian_request_status);
            }

            if ($("span[name='dian_request_status']").length > 0) {
                var dian_request_status = $("span[name='dian_request_status']").text();
                displayRequestStatus1(dian_request_status);
            }

            function displayRequestStatus1(dian_request_status) {
                if (dian_request_status == "FAIL") {
                    $(".status-requested-container").find(".fail").css("display", "block");
                    $(".status-requested-container").find(".ok").css("display", "none");
                    //alert("IN 1_1");
                } else if (dian_request_status == "OK") {
                    $(".status-requested-container").find(".fail").css("display", "none");
                    $(".status-requested-container").find(".ok").css("display", "block");
                    // alert("IN 1_2");
                } else {
                    $(".status-requested-container").find(".fail").css("display", "none");
                    $(".status-requested-container").find(".ok").css("display", "none");
                    $(".status-requested-container").find(".not_requested").fadeIn();
                    //alert("IN 1_3");
                }
            }

            var invoice_number = $("span[name=number]").text();
            var firstPart = invoice_number.substring(0, 2);
            if (firstPart == "fd" || firstPart == "fc") {
                $("button[name=202]").fadeOut();
                $("button[name=202]").find("span").text("Agregar Nota");
                $("button[name=202]").text("Agregar Nota");
                $(".o_statusbar_buttons button").each(function() {
                    var textButton = $(this).text();
                    if (textButton.toLowerCase() == "emitir rectificativa" || textButton.toLowerCase() == "emitir nota")
                        $(this).fadeOut();
                });
            }
            if (firstPart == "fv") {
                if (index_Exc == 0) {
                    var intervalIdFV = setInterval(function() {
                        var invoice_number = $("span[name=number]").text();
                        var data = { "params": { 'invoice_number': invoice_number } }
                        $.ajax({
                            type: "POST",
                            url: '/dianefact/can_create_notes',
                            data: JSON.stringify(data),
                            dataType: 'json',
                            contentType: "application/json",
                            async: false,
                            success: function(response) {

                                if (response.result.found == true) {
                                    console.log(response);
                                    $("span[name=number]").css("color", "red")
                                    $("span[name=number]").css("opacity", "0.8")
                                    $("span[name=number]").append("<div class='invoice-cancelled'>Factura anulada - " + response.result.number + "</div>");
                                    $("button[name=202]").fadeOut();
                                }
                                clearInterval(intervalIdFV);

                                // prevent second ajax call
                                index_Exc++;
                            }
                        });
                    }, 0);
                }
            }
            if (!flagLoaded) {
                // POS
                $(document).on("blur", "input.vat", function() {
                        var ruc = $("input.vat").val();
                        var data = { "params": { 'nit': ruc } }
                            //$.ajax({
                            //    type: "POST",
                            //    url: '/dianefact/get_nit',
                            //    data: JSON.stringify(data),
                            //    dataType: 'json',
                            //    contentType: "application/json",
                            //    async: false,
                            //    success: function(response) {
                            //        console.log(response)
                            //        if (response.result.status == "OK") {
                            //            $(".client-name").val(response.result.denominacion);
                            //            //$(".client-address-street").val(response.result.address);
                            //            //$(".client-address-city").val(response.result.city);
                            //            swal("La empresa es valida", "", "success");
                            //        } else {
                            //            swal(response.result.status, "", "warning");
                            //        }
                            //    }
                            //});
                    })
                    // Respartner
                $(document).on("blur", "input.res_partner_vat", function() {
                    var ruc = $("input.res_partner_vat").val();
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
                    //             $(".res_partner_name").val(response.result.denominacion);
                    //             $(".res_partner_name").val(response.result.denominacion);
                    //             $(".res_partner_matricula").val(response.result.dian_matricula)
                    //                 //$(".client-address-street").val(response.result.address);
                    //                 //$(".client-address-city").val(response.result.city);
                    //             swal("La empresa es valida", "", "success");
                    //         } else {
                    //             swal(response.result.status, "", "warning");
                    //         }
                    //     }
                    // });
                })


                flagLoaded = true;
                //$(document).on("click", ".payment-screen .button", function() {
                //    if ($(this).hasClass("next")) {
                //        var intervalId = setInterval(function() {
                //            var posTop = $(".pos-center-align").text();
                //            if (posTop != "") {
//
                //                var orderReference = posTop.split(" ");
                //                if(orderReference[2]=="")
                //                {
                //                    var posTop = $(".pos-order-reference").text();
                //                    orderReference = String(posTop).trim();
                //                }
                //                else
                //                {
                //                    orderReference = orderReference[2];
                //                }
                //                var data = { "params": { 'orderReference': orderReference } }
                //                $.ajax({
                //                    type: "POST",
                //                    url: '/dianefact/get_invoice_ordered',
                //                    data: JSON.stringify(data),
                //                    dataType: 'json',
                //                    contentType: "application/json",
                //                    async: false,
                //                    success: function(response) {
                //                        
                //                        if ($(".ticket_qr_image").length == 0) {
                //                            var qrImageHTML = "<div style='text-align:center'><img src='data:image/png;base64," + response.result.qr_image + "' width='100' height='100' class='ticket_qr_image'/><div>"
                //                            $(".pos-sale-ticket").append(qrImageHTML);
                //                            clearInterval(intervalId);
                //                        }
                //                        if ($(".invoice-details").length > 0) {
                //                            $(".invoice-journal").text(response.result.journal_name);
                //                            $(".invoice-number").text(response.result.number);
                //                            $(".invoice-details").fadeIn();
                //                            clearInterval(intervalId);
                //                        }
                //                    }
                //                });
                //            } else {
//
                //            }
//
                //        }, 2500);
                //    }
                //});

                $(document).on("click", ".js_invoice", function () {
                    if ($(this).hasClass("button")) {
                        var intervalIdInvoice = setInterval(function () {
                            var js_invoice = $(".js_invoice");
                            if (js_invoice.hasClass("highlight")) {
                                if ($(".journal-container-custom").length == 0) {
                                    $.ajax({
                                        type: "POST",
                                        url: '/dianefact/get_invoice_ticket_journal',
                                        data: JSON.stringify({}),
                                        dataType: 'json',
                                        contentType: "application/json",
                                        async: false,
                                        success: function (response) {
                                            if (response.result.journals != null && response.result.journals != '') {
                                                var journals = response.result.journals;
                                                var pos_config = response.result.pos_config;
                                                var option = '';
                                                journals.forEach(function (journal, index) {
                                                    if (journal.id > 0)
                                                        option += '<option value="' + journal.id + '">' + journal.name + '</option>';
                                                });
                                                
                                                if($('.journal-container-custom').length==0)
                                                    $(".payment-buttons").append("<div class='journal-container-custom'><label>Documento: </label><select id='journal_id' pos_id='" + pos_config.id + "' class='journal-pos-custom'>" + option + "</select><br><spam id='tipodocumentosec' class='popup popup-error'></spam></div>");
                                                
                                                
                                                //can't read classes from this addon default template definition, adding it on fire with jquery
                                                $(".journal-pos-custom").css("height", "38px");
                                                $(".journal-pos-custom").css("font-size", "16px");
                                                $(".journal-pos-custom").css("padding", "5px");
                                                $(".journal-pos-custom").css("margin-left", "0px");
                                                $(".journal-pos-custom").css("margin", "5px");
                                                $(".journal-container-custom").css("font-size", "18px");
                                                $("#journal_id").val(pos_config.invoice_journal_id);
                                            }

                                        }
                                    });
                                }
                                clearInterval(intervalIdInvoice);
                            }
                            clearInterval(intervalIdInvoice);
                        }, 100000);
                    }
                })

                $(document).on("change", "#journal_id", function() {
                    var intervalJournalSelect = setInterval(function() {
                        var pos_id = $("#journal_id").attr("pos_id");
                        console.log(pos_id)

                        var journal_new_id = $("#journal_id").val();
                        console.log(journal_new_id)
                        var data = { "params": { 'posID': pos_id, 'journalID': journal_new_id } }
                            //console.log(data)
                        $.ajax({
                            type: "POST",
                            url: '/dianefact/update_current_pos_conf',
                            data: JSON.stringify(data),
                            dataType: 'json',
                            contentType: "application/json",
                            async: false,
                            success: function(qrImage64) {
                                clearInterval(intervalJournalSelect);
                            }
                        });
                    }, 2500);
                })

            }
            if ($('.pos-content').length > 0) {
                if ($('.modal').length > 0) {
                    if ($(".modal-body:contains('ESTADO: FAIL')"))
                        $(".modal").fadeOut();

                    var popUpDisplayed = $(".popups").find('.modal-dialog:not(.oe_hidden)');
                    var titleText = popUpDisplayed.find(".title").html();
                    popUpDisplayed.find(".title").hide();
                    popUpDisplayed.find(".body").html(titleText)
                }
            }

           
        }, mainIntervalTime);


        
    });




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
})