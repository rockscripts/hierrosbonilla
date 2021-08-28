from odoo import models, fields, api, tools, _
import sys, json
from odoo.exceptions import Warning, UserError

class mail_template(models.Model):

    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
       
        res = None
        res = super(mail_template, self).generate_email(res_ids, fields)
        try:
            for res_id, template in self.get_email_template(res_ids).items():
                invoice = self.env['account.invoice'].browse(res_id)
                ubl_filename = invoice.signed_document_filename
                if(len(ubl_filename)>0):
                    ubl_attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.invoice'),
                        ('res_id', '=', res_id),
                        ('datas_fname', '=', ubl_filename)
                    ])
                    
                    if not ubl_attachments:
                        ubl_attachments = invoice._generate_email_ubl_attachment()

                    if(ubl_attachments):
                        if len(ubl_attachments) == 1 and template.report_name:
                            report_name = self._render_template(
                                template.report_name, template.model, res_id)
                            ext = '.xml'
                            if not report_name.endswith(ext):
                                report_name += ext
                            attachments = [(report_name, ubl_attachments.datas)]
                        else:
                            attachments = [(a.name, a.datas) for a in ubl_attachments]
                        res[res_id]['attachments'] += attachments
        except Exception as e:
            #with open('/odoo_dian_v12/custom/addons/dian_efact/log.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            exc_traceback = sys.exc_info()
            try:
                
                for res_id, template in self.get_email_template(res_ids).items():
                    guide = self.env['stock.picking'].browse(res_id)
                    #if(guide):
                    ubl_filename = guide.signed_document_filename
                    if(ubl_filename!=""):
                        ubl_attachments = self.env['ir.attachment'].search([
                            ('res_model', '=', 'stock.picking'),
                            ('res_id', '=', res_id),
                            ('datas_fname', '=', ubl_filename)
                        ])
                        if not ubl_attachments:
                            ubl_attachments = guide._generate_email_ubl_attachment()
                        if(ubl_attachments):
                            if len(ubl_attachments) == 1 and template.report_name:
                                report_name = self._render_template(
                                    template.report_name, template.model, res_id)
                                ext = '.XML'
                                if not report_name.endswith(ext):
                                    report_name += ext
                                attachments = [(report_name, ubl_attachments.datas)]
                            else:
                                attachments = [(a.name, a.datas) for a in ubl_attachments]
                            res[res_id]['attachments'] += attachments
            except Exception as e:
                exc_traceback = sys.exc_info()
                #with open('/odoo_sunatperu/custom/addons/sunat_fact/models/log.json', 'w') as outfile:
                #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
                return res
        return res