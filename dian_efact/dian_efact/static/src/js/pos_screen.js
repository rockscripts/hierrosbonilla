odoo.define('module.Sunat', function (require) 
{
    "use strict";
    var rpc = require('web.rpc');

    var screens = require('point_of_sale.screens');

    screens.ReceiptScreenWidget.include
    ({
        get_receipt_render_env: function () 
        {
            this.pos.last_receipt_render_env = this._super();
            var pos_edoc = this.pos_edoc();
            this.pos.get_order().to_invoice = true
            console.log(this.pos.get_order().to_invoice)
            
            if(pos_edoc)
            {
                if(pos_edoc['inv_id'])
                {
                    this.pos.last_receipt_render_env['ejournal_name'] = pos_edoc['journal_name'];
                    this.pos.last_receipt_render_env['ejournal_code'] = pos_edoc['journal_code'];
                    this.pos.last_receipt_render_env['enumber'] = pos_edoc['number'];
                    this.pos.last_receipt_render_env['ecufe'] = pos_edoc['cufe'];
                    //this.pos.last_receipt_render_env['total_letters'] = pos_edoc['total_letters'];                
                    this.pos.last_receipt_render_env['qr_image'] = window.location.origin + '/web/image?model=account.invoice&field=qr_image&id=' + pos_edoc['inv_id'];
                }                    
                else
                    this.pos.last_receipt_render_env['qr_image'] = false;
            }
            else
            {
                this.pos.last_receipt_render_env['qr_image'] = false;
            }            
            return this.pos.last_receipt_render_env;
        },
        pos_reference: function ()
        {
            var pos_reference = 0;            
            var data = { "params": {'pos_session_id':this.pos.pos_session.id } }
            $.ajax({
                        type: "POST",
                        url: '/dianefact/get_pos_reference',
                        data: JSON.stringify(data),
                        dataType: 'json',
                        contentType: "application/json",
                        async: false,
                        success: function(response) 
                            {
                                pos_reference = response.result
                                return pos_reference
                            }
                    });

            return pos_reference;
        },
        pos_edoc: function () {
            var order = this.pos.get_order();
            
            var orderID = order.name;
            console.log(orderID)
            if (orderID != "") {

                var data = { "params": { 'orderReference': orderID } }
                var result = [];
                $.ajax({
                    type: "POST",
                    url: '/dianefact/get_invoice_ordered',
                    data: JSON.stringify(data),
                    dataType: 'json',
                    contentType: "application/json",
                    async: false,
                    success: function (response) {
                        if(response.result)
                        {
                            result['qr_image'] = response.result.qr_image;
                            result['journal_name'] = response.result.journal_name;
                            result['journal_code'] = response.result.journal_code;
                            result['number'] = response.result.number;
                            result['ecufe'] = response.result.cufe;
                            result['inv_id'] = response.result.inv_id;
                            return result;
                        }
                        else
                            return false;
                    }

                });
                return result
            } else {

            }

            //}, 2500);
            // }
            //var response = set_invoice_details_einvoicing();
            //console.log(response);
        },
    });

    screens.PaymentScreenWidget.include
    ({
        renderElement: function () {
            var self = this;
            this._super();

            this.render_paymentlines();

            this.$('.back').click(function () {
                self.click_back();
            });

            this.$('.next').click(function () {
                self.validate_order();
            });

            this.$('.js_set_customer').click(function () {
                self.click_set_customer();
            });

            this.$('.js_tip').click(function () {
                self.click_tip();
            });
            this.$('.js_factura').click(function () {
                self.click_invoice_factura();
            });
            this.$('.js_email').click(function () {
                self.click_email();
            });
            this.$('.js_cashdrawer').click(function () {
                self.pos.proxy.printer.open_cashbox();
            });
            
            this.$('.js_give_invoice').click(function () 
            {
                var edoc_type = $(this).attr("edoc_type");
                if (edoc_type == "factura") {
                    self.click_invoice_factura();
                    $('.js_nota_venta').removeClass('highlight');
                    $('.js_pos_venta').removeClass('highlight');
                    $('.js_factura').addClass('highlight');
                }
                
                if (edoc_type == "nota_venta") {
                    self.click_invoice_nota_venta();
                    $('.js_factura').removeClass('highlight');
                    $('.js_pos_venta').removeClass('highlight');
                    $('.js_nota_venta').addClass('highlight');
                }    

                if (edoc_type == "pos_venta") {
                    self.click_invoice_pos_venta();
                    $('.js_factura').removeClass('highlight');
                    $('.js_nota_venta').removeClass('highlight');
                    $('.js_pos_venta').addClass('highlight');
                }    

                var pos_id = null;
                var journal_new_id = null;
                if ($(".js_give_invoice").length > 0)
                 {
                    $.ajax
                    ({
                        type: "POST",
                        url: '/dianefact/get_invoice_ticket_journal',
                        data: JSON.stringify({}),
                        dataType: 'json',
                        contentType: "application/json",
                        async: false,
                        success: function (response) 
                        {
                            if (response.result.journals != null && response.result.journals != '') 
                            {
                                var journals = response.result.journals;
                                var pos_config = response.result.pos_config;
                                var option = '';
                                var journal_factura_id = null;
                                var journal_nota_venta = null;
                                var journal_pos_venta = null;
                                var document_id = null;
                                journals.forEach(function (journal, index) 
                                {
                                    if (journal.id > 0) 
                                    {
                                        option += '<option value="' + journal.id + '">' + journal.name + '</option>';
                                        //console.log(journal.code)
                                        if (String(journal.code) == ('FAC') || String(journal.code) == ('INV') || String(journal.code) == ('EFACT')) 
                                        {
                                            journal_factura_id = journal.id;
                                            document_id = journal.id;
                                        }
                                        if (String(journal.code) == ('BOLV')) 
                                        {
                                            journal_nota_venta= journal.id;
                                            document_id = journal.id;
                                        }
                                        if (String(journal.code) == ('POSV')) 
                                        {
                                            journal_pos_venta= journal.id;
                                            document_id = journal.id;
                                        }
                                    }

                                });

                                var payment_buttons = $(".payment-buttons");
                                if($('.journal-container-custom').length==0)
                                    payment_buttons.append("<div class='journal-container-custom'><label>Documento: </label><select id='journal_id' pos_id='" + pos_config.id + "' class='journal-pos-custom'>" + option + "</select><br><spam id='tipodocumentosec' class='popup popup-error'></spam></div>");
                                
                                //can't read classes from this addon default template definition, adding it on fire with jquery
                                $(".journal-pos-custom").css("height", "38px");
                                $(".journal-pos-custom").css("font-size", "16px");
                                $(".journal-pos-custom").css("padding", "5px");
                                $(".journal-pos-custom").css("margin-left", "0px");
                                $(".journal-pos-custom").css("margin", "5px");
                                $(".journal-container-custom").css("font-size", "18px");
                                
                                $(".js_factura").attr("journal_id", journal_factura_id);
                                $(".js_nota_venta").attr("journal_id", journal_nota_venta);
                                $(".js_pos_venta").attr("journal_id", journal_pos_venta);

                                payment_buttons.find(".journal-container-custom").hide();

                                if(edoc_type=="factura")
                                {
                                    $("#journal_id").val(journal_factura_id);
                                    journal_new_id = journal_factura_id;
                                    pos_id = pos_config.id;
                                } 
                                
                                if(edoc_type=="nota_venta")
                                {
                                    $("#journal_id").val(journal_nota_venta);
                                    journal_new_id = journal_nota_venta;
                                    pos_id = pos_config.id;
                                }   

                                if(edoc_type=="pos_venta")
                                {
                                    $("#journal_id").val(journal_pos_venta);
                                    journal_new_id = journal_pos_venta;
                                    pos_id = pos_config.id;
                                }

                                var data = { "params": { 'posID': pos_id, 'journalID': journal_new_id } }
                                $.ajax
                                ({
                                    type: "POST",
                                    url: '/dianefact/update_current_pos_conf',
                                    data: JSON.stringify(data),
                                    dataType: 'json',
                                    contentType: "application/json",
                                    async: false,
                                    success: function (qrImage64) {}
                                });
                            }
                        }
                    });
                }
                else 
                {
                    var id_document = $(this).attr("journal_id");
                    $('#journal_id').val(id_document);
                    pos_id = $(".payment-buttons").find("#journal_id").attr("pos_id");
                    journal_new_id = $(".payment-buttons").find("#journal_id").val();
                }
            });
        },
        click_invoice_factura: function () {
            var order = this.pos.get_order();
            if(!order.is_to_invoice())
            {
               order.set_to_invoice(true); 
            }
            
            this.$('.js_factura').removeClass('highlight');
            if (order.is_to_invoice()) {
                this.$('.js_nota_venta').removeClass('highlight');
                this.$('.js_factura').addClass('highlight');
            } else {
                this.$('.js_nota_venta').removeClass('highlight');
                this.$('.js_factura').removeClass('highlight');
            }
        },

        click_invoice_nota_venta: function () {
            //alert("in")
            var order = this.pos.get_order();
            if(!order.is_to_invoice())
            {
               order.set_to_invoice(true); 
            }
            this.$('.js_factura').removeClass('highlight');
            if (order.is_to_invoice()) {
                this.$('.js_factura').removeClass('highlight');
                this.$('.js_nota_venta').addClass('highlight');
            } else {
                this.$('.js_factura').removeClass('highlight');
                this.$('.js_nota_venta').addClass('highlight');
            }
        },

        click_invoice_pos_venta: function () {
            //alert("in")
            var order = this.pos.get_order();
            if(!order.is_to_invoice())
            {
               order.set_to_invoice(true); 
            }
            this.$('.js_factura').removeClass('highlight');
            if (order.is_to_invoice()) {
                this.$('.js_factura').removeClass('highlight');
                this.$('.js_nota_venta').removeClass('highlight');
                this.$('.js_pos_venta').addClass('highlight');
            } else {
                this.$('.js_factura').removeClass('highlight');
                this.$('.js_nota_venta').removeClass('highlight');
                this.$('.js_pos_venta').addClass('highlight');
            }
        },
    });
});