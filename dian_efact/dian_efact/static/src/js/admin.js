odoo.define('module.DianBackend', function(require) {

    "use strict";
    var mainIntervalTime = 3500;
    var rpc = require('web.rpc');
    var session_info = odoo.session_info;
    /**
     * Define documents types
     */
    var docTypes = {}
    docTypes["13"] = "Cédula de ciudadanía";
    docTypes["31"] = "NIT";
    docTypes["41"] = "Pasaporte";

    var mainInterval = setInterval(function() {
            $(document).ready(function() {
                if ($(".dian-style").length > 0) {
                    //alert("in")
                    setInterval(function() {
                        var last_table_title = $(".tab-content").last().find(".tab-pane").first().find("table").last().find(".o_horizontal_separator").text()
                        console.log(last_table_title)
                            //alert(last_table_title)
                        if (last_table_title == "Configuración técnicaPermisos extraOtro") {
                            $(".tab-content").last().find(".tab-pane").first().find("table").last().remove();

                        }
                        $(".tab-content").last().find(".tab-pane").find("table").last().fadeIn();
                    }, 100);
                }

                var session = require('web.session');
                //console.log(session)
                if (session.company_id > 0) {
                    $("button.js_website").each(function(i) {
                        var data_website_id = $(this).attr("data-website-id");
                        var current_button = $(this)
                        rpc.query({

                            model: 'website',
                            method: 'websites_for_company',
                            args: ["", data_website_id]
                        }).then(function(website) {
                            if (website.company_id != session.company_id) {
                                current_button.remove();
                            }
                        });
                        if ($("button.js_website").length - 1 == i) {
                            $("button.js_website").fadeIn();
                        }
                    });
                }
                $(".dropdown-item").each(function() {
                    if ($(this).attr("data-menu-xmlid") == "dian_efact.sunat_edocs_menu_root") {
                        $(this).addClass("sunat_edocs_menu_root")
                    }
                })
                $(document).on("click", ".sunat_edocs_menu_root", function() {
                    var data = { "params": { "update_context": 'update_context' } }
                    $.ajax({
                        type: "POST",
                        url: '/dianefact/update_context',
                        data: JSON.stringify(data),
                        dataType: 'json',
                        contentType: "application/json",
                        async: false,
                        success: function(response) {}
                    });
                });
                $(document).on("blur", "input[name='vat']", function() 
                {
                    //if($(".pos-content").length>0)
                    {
                        var nit = $("input[name='vat']").val();
                        var dv = calcular_DV(nit);
                        console.log(dv)
                        $("input[name='vat_dv']").val(dv);
                        $("span[name='vat_dv']").val(dv);
                        var id = get_url_param('id')
                        var model = get_url_param('model')
                        
                        if(model!=null)
                            model = model.replace(".", "_")
                        else
                            model = String("res_partner")
                            id = $("input[name='partner_id']").val();
                        if(id == null )
                        {
                            id = $("input[name='id']").val();
                        }
                        if(id == null )
                        {
                            id = $("span[name='id']").text();
                        }
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
                    }
                    
                });

                remove_menu_items();
                $(document).on("click", ".product_codes_back", function() {
                    go_back_button_products_service_class();
                });
                $(document).on("click", ".selector_sunat_product_code", function() {
                    var wrapper = document.createElement('div');
                    wrapper.innerHTML = "<div class='sunat-row'><div class='segment-container'><h1>Segmento</h1><table id='sunat_segments'></table></div></div>" +
                        "<div class='sunat-row'><div class='families-container'><h4 id='segment-name-selected'></h4><table id='sunat_families'></table></div></div>" +
                        "<div class='sunat-row'><div class='classes-container'><h4 id='family-name-selected'></h4><table id='sunat_classes'></table></div></div>" +
                        "<div class='sunat-row'><div class='products-container'><h4 id='class-name-selected'></h4><table id='sunat_products'></table></div></div>";
                    swal({
                        html: true,
                        title: "Clasificación productos / servicios",
                        content: wrapper,
                        type: "success",
                        showCancelButton: true,
                        cancelButtonText: "OK",
                        closeOnCancel: true
                    });
                    populate_segments()
                    init_back_button_products_service_class();
                });

                $(document).on("click", "tr.set_segment", function() {
                    $("#segment-name-selected").text($(this).attr("name"));
                    $(".segment-container").hide();
                    populate_families($(this).attr("code"))
                    $(".families-container").fadeIn();

                });

                $(document).on("click", "tr.set_family", function() {
                    $("#family-name-selected").text($(this).attr("name"));
                    $(".families-container").hide();
                    populate_classes($(this).attr("code"))
                    $(".classes-container").fadeIn();
                });

                $(document).on("click", "tr.set_class", function() {
                    $("#class-name-selected").text($(this).attr("name"));
                    $(".classes-container").hide();
                    populate_products($(this).attr("code"))
                    $(".products-container").fadeIn();
                });

                $(document).on("click", "tr.set_product_classification", function() {
                    $(this).attr("code")
                    $(this).attr("name")
                    $(".ItemClassificationCode").val($(this).attr("code") + " -- " + $(this).attr("name"));
                    swal.close();
                });


                // Display QR Image in eDocs
                $(document).on("click", ".btn-emitir-edocs", function() {
                    var invoice_id = $(".edocs_document_id").text();
                    var data = { "params": { "invoice_id": invoice_id } }
                    $.ajax({
                        type: "POST",
                        url: '/dianefact/edocs_submit_invoice',
                        data: JSON.stringify(data),
                        dataType: 'json',
                        contentType: "application/json",
                        async: false,
                        success: function(response) {
                            if (response.result.api_message != undefined)
                                $("span[name='api_message']").text(response.result.api_message);

                            if (response.result.dian_request_status != undefined) {
                                $(".status-requested-container .status-requested-element").hide();
                                displayRequestStatus(response.result.dian_request_status);
                            }
                        }
                    });
                });

                if ($("span[name='qr_image']").length > 0) {
                    displayQRImage();
                }

                if ($(".edocs_number_invoice").length > 0) {
                    $(".o_list_buttons").hide();
                    $(document).on("click", "tr.o_data_row", function() {
                        displayQRImage();
                    });
                }

                $(document).on("click", ".btn-representante-create", function() {
                    if ($(".representantes-formu").length > 0) {
                        loadRepresentantForm();
                        $(".representantes-list").hide();
                        $(".representantes-form-container").fadeIn();
                        $(".btn-representante-save").attr("id_representant", "0");
                        $(".btn-representante-save").attr("id_company", session_info.company_id);
                        $(".input-on-edit").hide();
                    }
                });

                if ($(".company-general-information").length > 0) {
                    loadGeneralInformationByDocument();
                }
            });

            $(document).on("click", ".btn-representante-back", function() {

                if ($(".representantes-form-container").length > 0) {
                    $(".representantes-form-container").hide();
                    $(".representantes-list").fadeIn();
                    $(".input-on-edit").hide();
                }
            });

            $(document).on("click", ".btn-representante-save", function() {

                if ($(".representantes-form-container").length > 0) {
                    var id_representant = $(this).attr("id_representant");
                    var id_company = $(this).attr("id_company");
                    var doc_type = $("#doc_type").val();
                    var doc_number = $("#doc_number").val();
                    var name = $("#name").val();
                    var position = $("#position").val();
                    var address = $("#address").val();
                    if (doc_number == "" || name == "" || position == "" || address == "") {
                        swal({
                            title: "Campos Incompletos",
                            text: "El número de documento, nombre y dirección del representante son requeridos.",
                            type: "warning",
                            showCancelButton: true,
                            cancelButtonText: "OK",
                            closeOnCancel: true
                        });
                        return;
                    }
                    var data = { "params": { "id_company": id_company, "id_representant": id_representant, "doc_type": doc_type, "doc_number": doc_number, "name": name, "position": position, "address": address } }
                    $.ajax({
                        type: "POST",
                        url: '/dianefact/save_representants',
                        data: JSON.stringify(data),
                        dataType: 'json',
                        contentType: "application/json",
                        async: false,
                        success: function(response) {
                            if (response.result == false) {
                                swal({
                                    title: "Representante Duplicado",
                                    text: "Existe representante con la misma información",
                                    type: "warning",
                                    showCancelButton: true,
                                    cancelButtonText: "OK",
                                    closeOnCancel: true
                                });
                            } else {
                                swal({
                                    title: "Representante Guardado",
                                    text: "",
                                    type: "success",
                                    showCancelButton: true,
                                    cancelButtonText: "OK",
                                    closeOnCancel: true
                                });
                                populateDataRepresentantsList();
                                $(".representantes-form-container").hide();
                                $(".representantes-list").fadeIn();
                            }
                        }
                    });
                }
            })

            $(document).on("click", ".btn-representante-edit", function() {
                loadRepresentantForm()
                var data = [];
                data["representant_id"] = $(this).attr("representant_id");
                var rowContainer = $(".row-representant-" + data["representant_id"]);
                data["doc_type_num"] = rowContainer.find(".td-doc_type_num").val();
                data["doc_type"] = rowContainer.find(".td-doc_type").text();
                data["doc_number"] = rowContainer.find(".td-doc_number").text();
                data["name"] = rowContainer.find(".td-name").text();
                data["position"] = rowContainer.find(".td-position").text();
                data["address"] = rowContainer.find(".td-address").text();
                data["date_added"] = rowContainer.find(".td-date-created").val();


                $("#doc_type").val(data["doc_type_num"]);
                $("#doc_number").val(data["doc_number"]);
                $("#name").val(data["name"]);
                $("#position").val(data["position"]);
                $("#address").val(data["address"]);
                $("#date_added").val(data["date_added"]);
                $(".btn-representante-save").attr("id_representant", data["representant_id"]);
                $(".representantes-list").hide();
                $(".representantes-form-container").fadeIn();
                $(".input-on-edit").fadeIn();

            });
            $(document).on("click", ".btn-representante-remove", function() {
                swal({
                        title: "¿Esta seguro?",
                        text: "No se podrá recueprar una vez se haya eliminado",
                        icon: "warning",
                        buttons: true,
                        dangerMode: true,
                    })
                    .then((willDelete) => {
                        if (willDelete) {
                            var id_representant = $(this).attr("representant_id");
                            var data = { "params": { "id_representant": id_representant } }
                            $.ajax({
                                type: "POST",
                                url: '/dianefact/remove_representant',
                                data: JSON.stringify(data),
                                dataType: 'json',
                                contentType: "application/json",
                                async: false,
                                success: function(response) {
                                    populateDataRepresentantsList();
                                    $(".representantes-form-container").hide();
                                    $(".representantes-list").fadeIn();
                                }
                            });
                        }
                    });
            });

            /**
             * BG FIX: after clicks edit and save main odoo button representant table disapear
             */
            $(document).on("click", ".o_form_button_edit", function() {
                populateDataRepresentantsList();
                loadRepresentantForm();
            });

            $(document).on("click", ".o_form_button_create", function() {
                populateDataRepresentantsList();
                loadRepresentantForm();
            });
            /**
             * EOF FIX
             */

            if($(".representantes-list").length>0)
                populateDataRepresentantsList();
            clearInterval(mainInterval);
        },
        mainIntervalTime);
});

function displayQRImage() {
    var mainInterval = setInterval(function() {
        if ($("span[name='qr_image']").length > 0) {
            $("span[name='qr_image']").hide();
            var qr_image = $("span[name='qr_image']").text();
            $("span[name='qr_image']").html("<img src='data:PNG;base64," + qr_image + "' class='edocs-qrImage'>");
            $("span[name='qr_image']").fadeIn();
            clearInterval(mainInterval);
        }
    }, 200);
}

function populateDataRepresentantsList() {
    var docTypes = {}
    docTypes["13"] = "Cédula de ciudadanía";
    docTypes["31"] = "NIT";
    docTypes["41"] = "Pasaporte";
    var data = { "params": {} }
    $.ajax({
        type: "POST",
        url: '/dianefact/populate_representants_list',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            var representants = response.result;
            var representants_rows_container = $(".representantes-list").find(".table").find("tbody");
            representants_rows_container.html("");
            if (representants.length > 0) {
                representants.forEach(function(representant) {
                    var row = '<tr class="row-representant-' + representant.id + '"><td class="td-doc_type"><input type="hidden" class="td-doc_type_num" value="' + representant.doc_type + '"/>' + docTypes[representant.doc_type] + '</td><td  class="td-doc_number">' + representant.doc_number + '</td><td class="td-name">' + representant.name + '</td><td class="td-position">' + representant.position + '</td><td class="td-address">' + representant.address + '</td><td><div class="btn-actions"><div class="btn-custom-sunat btn-representante-edit btn-smaller" representant_id="' + representant.id + '"><i class="fa fa-edit"></i></div><div class="btn-custom-sunat btn-representante-remove btn-smaller btn-red" representant_id="' + representant.id + '"><i class="fa fa-trash"></i></div><input type="hidden" class="td-date-created" value="' + representant.date_added + '"/></div></td></tr>';
                    representants_rows_container.append(row);
                });
            } else {
                var row = '<tr><td colspan="6">Compañia sin representante legal</td></tr>';
                representants_rows_container.append(row);
            }

        }
    });
}
function populate_peruan_districts() {
    var data = { "params": {} }
    $.ajax({
        type: "POST",
        url: '/dianefact/populate_peruan_districts',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            console.log(response.result);
        }
    });
}
$(".dian_municipio")
function loadRepresentantForm() {
    var docTypes = {};
    docTypes["13"] = "Cédula de ciudadanía";
    docTypes["31"] = "NIT";
    docTypes["41"] = "Pasaporte";
    var form = '<div class="field-box">';
    form += '<label for="doc_type">Tipo de Documento</label>';
    form += '<div><select id="doc_type"><option value="13">Cédula de ciudadanía</option><option value="31">NIT</option><option value="41">Pasaporte</option></select></div>';
    form += '</div>';

    form += '<div class="field-box">';
    form += '<label for="doc_number">Número de Documento</label>';
    form += '<div><input id="doc_number" type="text"/></div>';
    form += '</div>';

    form += '<div class="field-box">';
    form += '<label for="name">Nombre</label>';
    form += '<div><input id="name" type="text"/></div>';
    form += '</div>';

    form += '<div class="field-box">';
    form += '<label for="position">Cargo</label>';
    form += '<div><input id="position" type="text"/></div>';
    form += '</div>';

    form += '<div class="field-box">';
    form += '<label for="address">Dirección</label>';
    form += '<div><input id="address" type="text"/></div>';
    form += '</div>';

    form += '<div class="field-box">';
    form += '<label class="input-on-edit"  for="date_added">Fecha desde</label>';
    form += '<div><input class="input-on-edit" id="date_added" type="text" disabled="disabled"/></div>';
    form += '</div>';

    $(".representantes-formu").html(form)
}

function loadGeneralInformationByDocument() {
    var documentNumber = $("span[name=vat]").val();
    $(".o_field_char").each(function(index, item) {
        if (item.getAttribute("name") == "vat") {
            documentNumber = $(item).text();
        }
    });
    if (parseInt(documentNumber) > 0) {
        var data = { "params": { "nit": documentNumber } }
            //$.ajax({
            //    type: "POST",
            //    url: '/dianefact/get_nit',
            //    data: JSON.stringify(data),
            //    dataType: 'json',
            //    contentType: "application/json",
            //    async: false,
            //    success: function(response) {
            //        console.log(response);
            //        //            response = response.result;
            //        //            if(response.status=="FAIL")
            //        //            {
            //        //                loadGeneralInformationByDocument();
            //        //            }
            //        //            else if(response.status=="OK")
            //        //            {
            //        //                var generalInformationHTML = '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="legal_name">Nombre legal</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                generalInformationHTML += '<div>'+response.name+'</div>';
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                generalInformationHTML += '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="nombre_comercial">Nombre comercial</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                generalInformationHTML += '<div>'+response.nombre_comercial+'</div>';
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                generalInformationHTML += '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="tipo_contribuyente">Tipo contribuyente</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                generalInformationHTML += '<div>'+response.tipo_contribuyente+'</div>';
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                generalInformationHTML += '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="sistema_emision_comprobante">Sistema de emisión</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                generalInformationHTML += '<div>'+response.sistema_emision_comprobante+'</div>';
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                generalInformationHTML += '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="sistema_contabilidad">Sistema de contabilidad</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                generalInformationHTML += '<div>'+response.sistema_contabilidad+'</div>';
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                generalInformationHTML += '<div class="field-box">';
            //        //                generalInformationHTML += '<label for="actividad_economica">Actividad económica</label>';
            //        //                generalInformationHTML += '<div>';
            //        //                var activities = response.actividad_economica
            //        //                if(response.actividad_economica.length>0)
            //        //                {
            //        //                    for(i=0;i<activities.length;i++)
            //        //                    {
            //        //                        generalInformationHTML += '<div>'+activities[i]+'</div>';
            //        //                    }
            //        //                }                        
            //        //                generalInformationHTML += '</div>';
            //        //                generalInformationHTML += '</div>';
            //        //
            //        //                $(".company-general-information-container").html(generalInformationHTML);
            //        //            }
            //        //            else
            //        //            {
            //        //                swal({
            //        //                        title: "Identificación Tributaria",
            //        //                        text: response.status,
            //        //                        type: "warning",
            //        //                        showCancelButton: true,
            //        //                        cancelButtonText: "OK",
            //        //                        closeOnCancel: true
            //        //                    }); 
            //        //            }
            //        //                
            //    }
            //});
    } else {

        // swal({
        //     title: "Identificación Tributaria",
        //     text: "Debe establecer la identificación tributaria.",
        //     type: "warning",
        //     showCancelButton: true,
        //     cancelButtonText: "OK",
        //     closeOnCancel: true
        //     });
    }
}

function displayRequestStatus(dian_request_status) {
    if (dian_request_status == "FAIL") {
        $(".status-requested-container").find(".fail").css("display", "block");
        $(".status-requested-container").find(".ok").css("display", "none");
        $("span[name='dian_request_status']").text(dian_request_status);
    } else if (dian_request_status == "OK") {
        $(".status-requested-container").find(".fail").css("display", "none");
        $(".status-requested-container").find(".ok").css("display", "block");
        $("span[name='dian_request_status']").text(dian_request_status);
    } else {
        $(".status-requested-container").find(".fail").css("display", "none");
        $(".status-requested-container").find(".ok").css("display", "none");
        $(".status-requested-container").find(".not_requested").fadeIn();
    }
}

function populate_segments() {
    $(".product_codes_back").hide();
    $(".product_codes_back").attr("state", "start");
    //populate segments
    var data = {
        "params": {
            'segment_code': ""
        }
    }
    $.ajax({
        type: "POST",
        url: '/dianefact/get_segments',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            if (typeof response.result !== undefined) {
                // $("select[name='families']").html("");
                var segments = response.result;
                $("table#sunat_segments").html("");
                segments.forEach(function(item) {
                    $("table#sunat_segments").append("<tr class='set_segment' name='" + item[1] + "' code='" + item[0] + "'> <td><b><small>" + item[0] + "  </small></b></td>" + "<td>" + item[1] + "</td>" + "</tr>");
                });
            }
        }
    });
}

function populate_families(segment_code) {
    $(".product_codes_back").fadeIn();
    $(".product_codes_back").attr("state", "1");
    var data = {
        "params": {
            'segment_code': segment_code.replace(/"([^"]+(?="))"/g, '$1')
        }
    }
    $.ajax({
        type: "POST",
        url: '/dianefact/get_families',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            if (typeof response.result !== undefined) {
                // $("select[name='families']").html("");
                var families = response.result;
                $("table#sunat_families").html("");
                families.forEach(function(item) {
                    $("table#sunat_families").append("<tr class='set_family' name='" + item[1] + "' code='" + item[0] + "'> <td><b><small>" + item[0] + "  </small></b></td>" + "<td>" + item[1] + "</td>" + "</tr>");
                });
            }
        }
    });
}

function populate_classes(family_code) {
    $(".product_codes_back").fadeIn();
    $(".product_codes_back").attr("state", "2");
    var data = {
        "params": {
            'family_code': family_code.replace(/"([^"]+(?="))"/g, '$1')
        }
    }
    $.ajax({
        type: "POST",
        url: '/dianefact/get_clases',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            if (typeof response.result !== undefined) {
                var clases = response.result;
                $("table#sunat_classes").html("");
                clases.forEach(function(item) {
                    $("table#sunat_classes").append("<tr class='set_class' name='" + item[1] + "' code='" + item[0] + "'> <td><b><small>" + item[0] + "  </small></b></td>" + "<td>" + item[1] + "</td>" + "</tr>");

                });
            }
        }
    });
}

function populate_products(class_code) {
    $(".product_codes_back").fadeIn();
    $(".product_codes_back").attr("state", "3");
    var data = {
        "params": {
            'class_code': class_code.replace(/"([^"]+(?="))"/g, '$1')
        }
    }
    $.ajax({
        type: "POST",
        url: '/dianefact/get_products',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        async: false,
        success: function(response) {
            if (typeof response.result !== undefined) {
                var clases = response.result;
                $("table#sunat_products").html("");
                clases.forEach(function(item) {
                    $("table#sunat_products").append("<tr class='set_product_classification' name='" + item[1] + "' code='" + item[0] + "'> <td><b><small>" + item[0] + "  </small></b></td>" + "<td>" + item[1] + "</td>" + "</tr>");
                });
            }
        }
    });
}

function init_back_button_products_service_class() {
    $(".swal-button-container").append('<button class="swal-button swal-button--cancel product_codes_back" state="start">Atrás</button>');
}

function go_back_button_products_service_class() {
    var state = $(".product_codes_back").attr("state");
    if (state == "start") {
        $(".product_codes_back").hide();
        $(".product_codes_back").attr("state", "start");
    }
    if (state == "1") {
        $(".product_codes_back").hide();
        $(".families-container").hide();
        $(".segment-container").fadeIn();
        $(".product_codes_back").attr("state", "start");
    }
    if (state == "2") {
        $(".classes-container").hide();
        $(".families-container").fadeIn();
        $(".product_codes_back").fadeIn();
        $(".product_codes_back").attr("state", "1");
    }
    if (state == "3") {
        $(".product_codes_back").fadeIn();
        $(".products-container").hide();
        $(".classes-container").fadeIn();
        $(".product_codes_back").attr("state", "2");
    }
}

function remove_menu_items() {
    if ($(".dropdown-menu").length > 0) {
        $(".dropdown-menu a").each(function(i, item) {
            var menu_xmlid = $(this).attr("data-menu-xmlid")
            if (menu_xmlid == "website.menu_website_add_features") {
                $(this).remove()
            }
        });
    }
}

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
        console.log ( y + "x" + vpri[z-i] + ":" ) ;

        x += (y * vpri[z - i]);
        console.log ( x ) ;    
    }

    y = x % 11;
    console.log ( y ) ;

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