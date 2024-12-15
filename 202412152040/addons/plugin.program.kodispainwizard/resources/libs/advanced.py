################################################################################
#      Copyright (C) 2019 drinfernoo                                           #
#                                                                              #
#  This Program is free software; you can redistribute it and/or modify        #
#  it under the terms of the GNU General Public License as published by        #
#  the Free Software Foundation; either version 2, or (at your option)         #
#  any later version.                                                          #
#                                                                              #
#  This Program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with XBMC; see the file COPYING.  If not, write to                    #
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.       #
#  http://www.gnu.org/copyleft/gpl.html                                        #
################################################################################

import xbmc
import xbmcgui

import os

from resources.libs.common.config import CONFIG
from resources.libs.common import directory
from resources.libs.common import logging
from resources.libs.common import tools
from resources.libs.gui import window


def view_current():
    window.show_text_box(CONFIG.ADDONTITLE, tools.read_from_file(CONFIG.ADVANCED).replace('\t', '    '))


def remove_current():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(CONFIG.ADDONTITLE, "[COLOR {0}]¿Estás seguro de que quieres eliminar el actual advancedsettings.xml?[/COLOR]".format(CONFIG.COLOR2),
                                           yeslabel="[B][COLOR white]SI[/COLOR][/B]",
                                           nolabel="[B][COLOR white]NO[/COLOR][/B]")

    if ok:
        if os.path.exists(CONFIG.ADVANCED):
            tools.remove_file(CONFIG.ADVANCED)
            logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               "[COLOR {0}]advancedsettings.xml eliminado[/COLOR]".format(CONFIG.COLOR2))
            xbmc.executebuiltin('Container.Refresh()')
        else:
            logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               "[COLOR {0}]advancedsettings.xml no encontrado[/COLOR]".format(CONFIG.COLOR2))
    else:
        logging.log_notify("[COLOR {0}]{1}[/COLOR]".format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               "[COLOR {0}]advancedsettings.xml no eliminado[/COLOR]".format(CONFIG.COLOR2))


def _write_setting(category, tag, value):
    from xml.etree import ElementTree

    exists = os.path.exists(CONFIG.ADVANCED)

    if exists:
        root = ElementTree.parse(CONFIG.ADVANCED).getroot()
    else:
        root = ElementTree.Element('advancedsettings')

    tree_category = root.find('./{0}'.format(category))
    if tree_category is None:
        tree_category = ElementTree.SubElement(root, category)

    category_tag = tree_category.find(tag)
    if category_tag is None:
        category_tag = ElementTree.SubElement(tree_category, tag)

    category_tag.text = '{0}'.format(value)

    tree = ElementTree.ElementTree(root)

    logging.log('Writing {0} - {1}: {2} to advancedsettings.xml'.format(category, tag, value), level=xbmc.LOGDEBUG)
    tree.write(CONFIG.ADVANCED)

    xbmc.executebuiltin('Container.Refresh()')


class AdvancedMenu:
    def __init__(self):
        self.dialog = xbmcgui.Dialog()

        self.tags = {}

    def show_menu(self, url=None):
        directory.add_dir('Configuracion rapida advancedsettings.xml',
                               {'mode': 'advanced_settings', 'action': 'quick_configure'}, icon=CONFIG.ICONMAINT,
                               themeit=CONFIG.THEME3)

        if os.path.exists(CONFIG.ADVANCED):
            directory.add_file('Ver actual advancedsettings.xml',
                               {'mode': 'advanced_settings', 'action': 'view_current'}, icon=CONFIG.ICONMAINT,
                               themeit=CONFIG.THEME3)
            directory.add_file('Eliminar actual advancedsettings.xml',
                               {'mode': 'advanced_settings', 'action': 'remove_current'}, icon=CONFIG.ICONMAINT,
                               themeit=CONFIG.THEME3)
        
        response = tools.open_url(CONFIG.ADVANCEDFILE)
        url_response = tools.open_url(url)
        local_file = os.path.join(CONFIG.ADDON_PATH, 'resources', 'text', 'advanced.json')

        if url_response:
            TEMPADVANCEDFILE = url_response.text
        elif response:
            TEMPADVANCEDFILE = response.text
        elif os.path.exists(local_file):
            TEMPADVANCEDFILE = tools.read_from_file(local_file)
        else:
            TEMPADVANCEDFILE = None
            logging.log("[Advanced Settings] No Presets Available")
        
        if TEMPADVANCEDFILE:
            import json

            directory.add_separator(icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
            
            try:
                advanced_json = json.loads(TEMPADVANCEDFILE)
            except:
                advanced_json = None
                logging.log("[Advanced Settings] ERROR: Invalid Format for {0}.".format(TEMPADVANCEDFILE))
                
            if advanced_json:
                presets = advanced_json['presets']
                if presets and len(presets) > 0:
                    for preset in presets:
                        name = preset.get('name', '')
                        section = preset.get('section', False)
                        preseturl = preset.get('url', '')
                        icon = preset.get('icon', CONFIG.ADDON_ICON)
                        fanart = preset.get('fanart', CONFIG.ADDON_FANART)
                        description = preset.get('description', '')

                        if not name:
                            logging.log('[Advanced Settings] Missing tag \'name\'', level=xbmc.LOGDEBUG)
                            continue
                        if not preseturl:
                            logging.log('[Advanced Settings] Missing tag \'url\'', level=xbmc.LOGDEBUG)
                            continue
                        
                        if section:
                            directory.add_dir(name, {'mode': 'advanced_settings', 'url': preseturl},
                                              description=description, icon=icon, fanart=fanart, themeit=CONFIG.THEME3)
                        else:
                            directory.add_file(name,
                                               {'mode': 'advanced_settings', 'action': 'write_advanced', 'name': name,
                                                'url': preseturl},
                                               description=description, icon=icon, fanart=fanart, themeit=CONFIG.THEME2)
        else:
            logging.log("[Advanced Settings] URL not working: {0}".format(CONFIG.ADVANCEDFILE))

    def quick_configure(self):
        directory.add_file('Los cambios no se reflejarán hasta que se reinicie Kodi.', icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        directory.add_file('Click here to restart Kodi.', {'mode': 'forceclose'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        directory.add_file('Pronto habrá más categorías :)', icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        directory.add_separator(middle='CATEGORIAS')
        # directory.add_dir('Troubleshooting', {'mode': 'advanced_settings', 'action': 'show_section', 'tags': 'loglevel|jsonrpc'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        # directory.add_dir('Playback', {'mode': 'advanced_settings', 'action': 'show_section', 'tags': 'skiploopfilter|video|audio|edl|pvr|epg|forcedswaptime'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        # directory.add_dir('Video Library', {'mode': 'advanced_settings', 'action': 'show_section', 'tags': 'videoextensions|discstubextensions|languagecodes|moviestacking|folderstacking|cleandatetime|cleanstrings|tvshowmatching|tvmultipartmatching'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
        directory.add_dir('Red y cache', {'mode': 'advanced_settings', 'action': 'show_section', 'tags': 'cache|network'}, icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)

    def show_section(self, tags):
        from xml.etree import ElementTree

        split_tags = tags.split('|')
        logging.log(split_tags)

        exists = os.path.exists(CONFIG.ADVANCED)

        if exists:
            root = ElementTree.parse(CONFIG.ADVANCED).getroot()

            for category in root.findall('*'):
                name = category.tag
                if name not in split_tags:
                    continue

                values = {}

                for element in category.findall('*'):
                    values[element.tag] = element.text

                self.tags[name] = values

        if len(self.tags) == 0:
            directory.add_file('No existe ninguna configuracion para esta categoria en su archivo advancedsettings.xml actual.', icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)
            directory.add_separator()
            
        for category in self.tags:
            directory.add_separator(category.upper())

            for tag in self.tags[category]:
                value = self.tags[category][tag]

                if value is None:
                    value = ''

                directory.add_file('{0}: {1}'.format(tag, value), {'mode': 'advanced_settings', 'action': 'set_setting',
                                                                   'category': category, 'tag': tag, 'value': value},
                                   icon=CONFIG.ICONMAINT, themeit=CONFIG.THEME3)

    def set_setting(self, category, tag, current):
        value = None
        
        if category == 'cache':
            value = self._cache(tag, current)
        elif category == 'network':
            value = self._network(tag, current)
            
        if value:
            _write_setting(category, tag, value)
            
    def _cache(self, tag, current):
        value = None
        
        if tag == 'buffermode':
            values = ['Buffer de todos los sistemas de archivos de Internet',
                      'Buffer de todos los sistemas de archivos',
                      'Sólo buffer de los verdaderos sistemas de archivos de Internet',
                      'No buffer',
                      'Todos los sistemas de archivos de red']
                      
            items = []
            for i in range(len(values)):
                items.append(xbmcgui.ListItem(label=str(i), label2=values[i]))
                      
            value = self.dialog.select('Choose a Value', items, preselect=int(current), useDetails=True)
        elif tag == 'memorysize':
            free_memory = tools.get_info_label('System.Memory(free)')
            free_converted = tools.convert_size(int(float(free_memory[:-2])) * 1024 * 1024)
            
            recommended = int(float(free_memory[:-2]) / 3) * 1024 * 1024
            recommended_converted = tools.convert_size(int(float(free_memory[:-2]) / 3) * 1024 * 1024)
        
            value = tools.get_keyboard(default='{0}'.format(recommended), heading='Tamaño de la memoria en bytes\n(Recomendado: {0} = {1})'.format(recommended_converted, recommended))
        elif tag == 'readfactor':
            value = tools.get_keyboard(default='{0}'.format(current), heading='Indice de llenado de cache\n(Las cifras elevadas provocaran un gran uso del ancho de banda!)')
            
        return value
            
    def _network(self, tag, current):
        msgs = {'curlclienttimeout': 'Timeout in seconds for libcurl (http/ftp) connections',
                'curllowspeedtime': 'Time in seconds for libcurl to consider a connection lowspeed',
                'curlretries': 'Amount of retries for certain failed libcurl operations (e.g. timeout)',
                'httpproxyusername': 'Username for Basic Proxy Authentication',
                'httpproxypassword': 'Password for Basic Proxy Authentication'}
        
        value = tools.get_keyboard(default='{0}'.format(current), heading=msgs[tag])
            
        return value
                
    def write_advanced(self, name, url):
        response = tools.open_url(url)

        if response:
            if os.path.exists(CONFIG.ADVANCED):
                choice = self.dialog.yesno(CONFIG.ADDONTITLE,
                                           "[COLOR {0}]¿Desea sobrescribir su configuración avanzada actual con [COLOR {1}]{2}[/COLOR]?[/COLOR]".format(
                                               CONFIG.COLOR2, CONFIG.COLOR1, name),
                                           yeslabel="[B][COLOR white]SI[/COLOR][/B]",
                                           nolabel="[B][COLOR white]NO[/COLOR][/B]")
            else:
                choice = self.dialog.yesno(CONFIG.ADDONTITLE,
                                           "[COLOR {0}]¿Desea descargar e instalar [COLOR {1}]{2}[/COLOR]?[/COLOR]".format(
                                               CONFIG.COLOR2, CONFIG.COLOR1, name),
                                           yeslabel="[B][COLOR white]SI[/COLOR][/B]",
                                           nolabel="[B][COLOR white]NO[/COLOR][/B]")

            if choice == 1:
                tools.write_to_file(CONFIG.ADVANCED, response.text)
                tools.kill_kodi(msg='[COLOR {0}]La nueva configuracion de advancedsettings.xml ha sido escrita con exito, pero los cambios no tendran efecto hasta que cierre Kodi.[/COLOR]'.format(
                                   CONFIG.COLOR2))
            else:
                logging.log("[Advanced Settings] install canceled")
                logging.log_notify('[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                                   "[COLOR {0}]Escritura cancelada![/COLOR]".format(CONFIG.COLOR2))
                return
        else:
            logging.log("[Advanced Settings] URL not working: {0}".format(url))
            logging.log_notify('[COLOR {0}]{1}[/COLOR]'.format(CONFIG.COLOR1, CONFIG.ADDONTITLE),
                               "[COLOR {0}]La URL no funciona[/COLOR]".format(CONFIG.COLOR2))
