JAZZMIN_UI_TWEAKS = {
   'theme': 'cosmo',
}

JAZZMIN_SETTINGS = {
   'site_logo' : 'sensolog.png',
   'login_logo': 'sensolog.png',
   'site_icon': 'sensolog.png',
   
   'site_logo_classes': 'img-circle',

   'welcome_sign': "Sensolog Superadmin",
   'copyright': "Sensolog",

   'topmenu_links': [
      {'name': 'Home',  'url': '/admin',},
      {'name': 'Support', 'url': 'https://techcolab.org', 'new_window': True},
   ],

   'usermenu_links': [
      {'name': 'Support', 'url': 'https://techcolab.org', 'new_window': True},
      {'model': 'auth.user'}
   ],
   
   'related_modal_active': True,
   'use_google_fonts_cdn': True,
   # 'show_ui_builder': True,

# ADD THESE LINES:
   "custom_css": None,
   "custom_js": None,

}