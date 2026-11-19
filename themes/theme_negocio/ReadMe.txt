Download theme_negocio module
1. Go to theme_negocio/code folder
2. Cut all folders and move these folder into your addons path / custom addon path
3. Open theme_negocio folder __manifest__.py file
4. Replace 'depends': [''website_theme_install'] line with 'depends': ['negocio_web','website_theme_install']
5. Go to apps and update applist.
6. Click on install negocio_web . 
7. Also after performing this restart the odoo services.
