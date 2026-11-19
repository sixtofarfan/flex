from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from addons.lunch.models.lunch_supplier import float_to_time, time_to_float
import odoo
import logging
import threading
import odoo.tools as tools
_logger = logging.getLogger(__name__)

class ReliablePartners(models.Model):
    _name = "reliable.partners"
    _description = "Trusted By Slider"
    _order = "id desc"
    
    image = fields.Binary(
        "Logo", attachment=True,)
    filename = fields.Char()
    
class CustomersReviews(models.Model):
    _name = "customers.reviews"
    _description = "Testimonials"
    _order = "id desc"
    
    customer_id = fields.Many2one('res.partner',string="Customer")
    review = fields.Text("Review")
    image = fields.Binary("Image",related='customer_id.image_1920')
    
class WebsiteMeetingInfo(models.Model):
    _name ="website.meeting.info"
    _description = "Website Meeting Information"
    _order = "id desc"
    
    name = fields.Char("Customer",required=True)
    email = fields.Char("Email",required=True)
    meeting_date = fields.Date("Meeting Date")
    meeting_time = fields.Char("Meeting Time")
    meeting_datetime = fields.Char("Meeting Date str",required=True)
    mtime = fields.Char("Mtime",required=True)
    phone = fields.Char("Phone",required=True)
    question = fields.Text("Message",required=True)
    subject = fields.Char("Subject")
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('meeting_datetime'):
                date = vals.get('meeting_datetime')
                dt = datetime.strptime(date , '%Y-%m-%d')
                vals['meeting_date'] = dt
            if vals.get('mtime'):
                mtime1 = vals.get('mtime')
                vals['meeting_time'] = str(mtime1)
                
        return super(WebsiteMeetingInfo, self).create(vals_list)
    
class WebsiteContactInfo(models.Model):
    _name ="website.contact.info"
    _description = "Website Contact Information"
    _order = "id desc"
    
    name = fields.Char("Customer",required=True)
    email = fields.Char("Email",required=True)
    subject = fields.Char("Subject",required=True)
    question = fields.Text("Message",required=True)
    
    @api.model_create_multi
    def create(self,vals):
        res = super(WebsiteContactInfo, self).create(vals)
        
#         if "subject" in vals.keys() and vals['subject']:
        if vals[0]['subject']:
            values = {
                'name' : vals[0]['subject'],
                'contact_name' : vals[0]['name'],
                'email_from' : vals[0]['email'],
                'description' : vals[0]['question'],
                'medium_id' : self.env.ref('utm.utm_medium_website').id,
                }
            self.env['crm.lead'].create(values) 
        return res
    
class ResCompany(models.Model):
    _inherit = "res.company"
    
    website_iframe=fields.Text("Iframe")
    social_googleplus = fields.Char('Google+ Account')
    
 
class LoadDemo(models.TransientModel):

    _name = 'load.demo'
    _description = 'Load Demo'

    def install_demo(self):
        force_demo_custom(self,self.env.cr)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/web',
        }        

# bese default method odoo demo data Oading Demo Data
def load_data(cr, idref, mode, kind, package, report):
    """

    kind: data, demo, test, init_xml, update_xml, demo_xml.

    noupdate is False, unless it is demo data or it is csv data in
    init mode.

    """
    def _get_files_of_kind(kind):
        if kind == 'demo':
            kind = ['demo_xml', 'demo']
        elif kind == 'data':
            kind = ['init_xml', 'update_xml', 'data']
        if isinstance(kind, str):
            kind = [kind]
        files = []
        for k in kind:
            for f in package.data[k]:
                files.append(f)
                if k.endswith('_xml') and not (k == 'init_xml' and not f.endswith('.xml')):
                    # init_xml, update_xml and demo_xml are deprecated except
                    # for the case of init_xml with csv and sql files as
                    # we can't specify noupdate for those file.
                    correct_key = 'demo' if k.count('demo') else 'data'
                    _logger.warning(
                        "module %s: key '%s' is deprecated in favor of '%s' for file '%s'.",
                        package.name, k, correct_key, f
                    )
        return files

    try:
        if kind in ('demo', 'test'):
            threading.currentThread().testing = True
        for filename in _get_files_of_kind(kind):
            _logger.info("loading %s/%s", package.name, filename)
            noupdate = False
            if kind in ('demo', 'demo_xml') or (filename.endswith('.csv') and kind in ('init', 'init_xml')):
                noupdate = True
            tools.convert_file(cr, package.name, filename, idref, mode, noupdate, kind, report)
    finally:
        if kind in ('demo', 'test'):
            threading.currentThread().testing = False
            
# get the data xml file frommodule           
def load_demo_custom(cr, package, idref, mode, report=None):
    """
    Loads demo data for the specified package.
    """
#     if not package.should_have_demo():
#         return False
    try:
        _logger.info("Module %s: loading demo", package.name)
        with cr.savepoint(flush=False):
            load_data(cr, idref, mode, kind='demo', package=package, report=report)
        return True
    except Exception as e:
        # If we could not install demo data for this module
        _logger.warning(
            "Module %s demo data failed to install, installed without demo data",
            package.name, exc_info=True)

        env = api.Environment(cr, SUPERUSER_ID, {})
        todo = env.ref('base.demo_failure_todo', raise_if_not_found=False)
        Failure = env.get('ir.demo_failure')
        if todo and Failure is not None:
            todo.state = 'open'
            Failure.create({'module_id': package.id, 'error': str(e)})
        return False      
      
# custom method  to install demo data     
def force_demo_custom(self,cr):
    """
    Forces the `demo` flag on custom modules, and installs demo data for custom installed modules.
    """
    # get  custom module name if demo data not load
    ir_module_obj = self.env["ir.module.module"].search([('name','=','theme_plus')])
    if ir_module_obj.demo == False:
        graph = odoo.modules.graph.Graph()
        cr.execute("UPDATE ir_module_module SET demo=True where name='theme_plus'")
        cr.execute(
            "SELECT name FROM ir_module_module WHERE state IN ('installed', 'to upgrade', 'to remove')"
        )
        module_list = [name for (name,) in cr.fetchall()]
        graph.add_modules(cr, module_list, ['demo'])
        for package in graph:
            if package.name == 'theme_plus':
                load_demo_custom(cr, package, {}, 'init')
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['ir.module.module'].invalidate_cache(['demo'])
        
    # if demo data load install time that generate warning
    else:
        raise UserError(_("Already Install Demo Data."))
        
