################################################################################
#      Copyright (C) 2015 Surfacingx                                           #
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
import xbmcvfs

import os

import six

if six.PY3:
    import zipfile
elif six.PY2:
    from resources.libs import zipfile

from resources.libs.common import logging
from resources.libs.common import tools
from resources.libs.common.config import CONFIG


def binaries():
    dialog = xbmcgui.Dialog()

    binarytxt = os.path.join(CONFIG.USERDATA, 'build_binaries.txt')

    if os.path.exists(binarytxt):
        binaryids = tools.read_from_file(binarytxt).split(',')

        logging.log("[Binary Detection] Reinstalling Eligible Binary Addons")
        dialog.ok(CONFIG.ADDONTITLE,
                  '[COLOR {0}]La build restaurada contiene addons especificos de plataforma que ahora seran '
                  'automaticamente instalados. Durante este proceso pueden aparecer varios dialogos. Cancelarlos '
                  'puede hacer que la build restaurada funcione de forma incorrecta.[/COLOR]'.format(
                      CONFIG.COLOR2))
    else:
        logging.log("[Binary Detection] No Eligible Binary Addons to Reinstall")
        return True

    success = []
    fail = []

    if len(binaryids) == 0:
        logging.log('No addons selected for installation.')
        return

    from resources.libs.gui import addon_menu

    # finally, reinstall addons
    for addonid in binaryids:
        if addon_menu.install_from_kodi(addonid):
            logging.log('{0} install succeeded.'.format(addonid))
            success.append(addonid)
        else:
            logging.log('{0} install failed.'.format(addonid))
            fail.append(addonid)

    if not fail:
        dialog.ok(CONFIG.ADDONTITLE, 'Los addons seleccionados se han instalado correctamente.')
        os.remove(binarytxt)
        return True
    else:
        dialog.ok(CONFIG.ADDONTITLE, 'Los siguientes addons no se han podido instalar:\n{0}'.format(', '.join(fail)))
        return False


class Restore:
    def __init__(self, external=False):
        tools.ensure_folders()

        self.external = external
        self.dialog = xbmcgui.Dialog()
        self.progress_dialog = xbmcgui.DialogProgress()

    def _prompt_for_wipe(self):
        # Should we wipe first?
        wipe = self.dialog.yesno(CONFIG.ADDONTITLE,
                                 "[COLOR {0}]¿Desea restaurar su".format(CONFIG.COLOR2) + '\n' + "configuracion de Kodi a los valores predeterminados" + '\n' + "antes de instalar la {0} copia de seguridad?[/COLOR]".format('local' if not self.external else 'external'),
                                 nolabel='[B][COLOR white]NO[/COLOR][/B]',
                                 yeslabel='[B][COLOR white]SI[/COLOR][/B]')

        if wipe:
            from resources.libs import install
            install.wipe()

    def _from_file(self, file, loc):
        from resources.libs import db
        from resources.libs import extract

        display = os.path.split(file)
        filename = display[1]
        packages = os.path.join(CONFIG.PACKAGES, filename)

        if not self.external:
            try:
                zipfile.ZipFile(file, 'r', allowZip64=True)
            except zipfile.BadZipFile as e:
                from resources.libs.common import logging
                logging.log(e, level=xbmc.LOGERROR)
                self.progress_dialog.update(0, '[COLOR {0}]No se puede leer el archivo zip desde la ubicacion actual.'.format(CONFIG.COLOR2) + '\n' + 'Copiando archivo a paquetes')
                xbmcvfs.copy(file, packages)
                file = xbmcvfs.translatePath(packages)
                self.progress_dialog.update(0, '\n' + 'Copiando archivo a paquetes: Completo')
                zipfile.ZipFile(file, 'r', allowZip64=True)
        else:
            from resources.libs.downloader import Downloader
            Downloader().download(file, packages)

        self._prompt_for_wipe()

        self.progress_dialog.update(0, 'Instalando Copia de Seguridad Externa' + '\n' + 'Por favor, espere')
        percent, errors, error = extract.all(file, loc)
        self._view_errors(percent, errors, error, file)

        CONFIG.set_setting('installed', 'true')
        CONFIG.set_setting('extract', percent)
        CONFIG.set_setting('errors', errors)

        if self.external:
            try:
                os.remove(file)
            except:
                pass

        db.force_check_updates(over=True)

        tools.kill_kodi(
            msg='[COLOR {0}]Para guardar los cambios, hay que forzar el cierre de Kodi. ¿Desea continuar?[/COLOR]'.format(
                CONFIG.COLOR2))

    def _view_errors(self, percent, errors, error, file):
        if int(errors) >= 1:
            if self.dialog.yesno(CONFIG.ADDONTITLE, '[COLOR {0}][COLOR {1}]{2}[/COLOR]'.format(CONFIG.COLOR2, CONFIG.COLOR1, file) + '\n' + 'Completado: [COLOR {0}]{1}{2}[/COLOR] [Errores: [COLOR {3}]{4}[/COLOR]]'.format(CONFIG.COLOR1, percent, '%',CONFIG.COLOR1, errors) + '\n' + '¿Quiere ver los errores?[/COLOR]',
                                 nolabel='[B][COLOR white]NO[/COLOR][/B]',
                                 yeslabel='[B][COLOR white]SI[/COLOR][/B]'):

                from resources.libs.gui import window
                window.show_text_box("Visualizando Errores", error.replace('\t', ''))

    def choose(self, location):
        from resources.libs import skin

        skin.look_and_feel_data('restore')
        external = 'External' if self.external else 'Local'

        file = self.dialog.browseSingle(1, '[COLOR {0}]Seleccione el archivo de copia de seguridad que desea restaurar[/COLOR]'.format(
            CONFIG.COLOR2), '' if self.external else 'files', mask='.zip', useThumbs=True,
                                        defaultt=None if self.external else CONFIG.MYBUILDS)

        if not file.endswith('.zip'):
            logging.log_notify(CONFIG.ADDONTITLE,
                               "[COLOR {0}]{1} Restaurar: Cancelado[/COLOR]".format(
                                   CONFIG.COLOR2, external))
            return

        if self.external:
            from resources.libs.common import tools
            response = tools.open_url(file, check=True)

            if not response:
                logging.log_notify(CONFIG.ADDONTITLE,
                                   "[COLOR {0}]Restauracion externa: URL no valida[/COLOR]".format(CONFIG.COLOR2))
                return

        skin.skin_to_default("Restore")
        self.progress_dialog.create(CONFIG.ADDONTITLE, '[COLOR {0}]Instalando {1} Backup'.format(CONFIG.COLOR2, external) + '\n' + 'Por favor, espere[/COLOR]')

        self._from_file(file, location)


def restore(action, external=False):
    cls = Restore(external)

    if action == 'build':
        cls.choose(CONFIG.HOME)  # Install into special://home/
    elif action in ['gui', 'theme', 'addonpack']:
        cls.choose(CONFIG.USERDATA)  # Install into special://userdata/
    elif action == 'addondata':
        cls.choose(CONFIG.ADDON_DATA)  # Install into special://userdata/addon_data/
    elif action == 'binaries':
        binaries()
