# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Enzo Sierra (enzogael57@gmail.com)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

DEFAULT_VERSION = '1.0'

DEEPPTMPRED_DIC = {
    'name': 'DeepPTMPred',
    'version': DEFAULT_VERSION,
    'home': 'DEEPPTMPRED_HOME',
    'activation': 'DEEPPTMPRED_ACTIVATION_CMD',
    'esm_checkpoint': 'DEEPPTMPRED_ESM_CHECKPOINT',
}

READ_URL = 'https://github.com/Lvera-code/scipion-chem-deepptmpred'
UPSTREAM_URL = 'https://github.com/kuikui-wang/DeepPTMPred'

# Confirmado leyendo el runner vendorizado (scripts/deepptmpred_runner.py::
# _extract_esm_features, linea ~101): 'torch.device("cuda" if
# torch.cuda.is_available() else "cpu")' -- se decide EN CODIGO, sin ningun
# flag de CLI que exponer (a diferencia de TMbed/DiscoTope-3.0, los unicos 2
# plugins del proyecto 1 con un flag de GPU real). No se agrega parametro
# useGPU al protocolo (mismo criterio aplicado a DeepMVP).
GPU_REQUIRED = True

# Licencia de DeepPTMPred (upstream): el repo no declara LICENSE propia,
# pero el paper es CC BY-NC 4.0 (Oxford University Press) y Junwen Wang
# (autor de correspondencia) confirmo por email el 2026-07-29 que el codigo
# sigue los mismos terminos -- uso no comercial (TFG/CNB-CSIC, institucion
# publica) cubierto sin problema. Verificado en
# PTM-Prediction/STATUS.md linea ~206-215, no asumido.
LICENSE_NOTE = (
    'CC BY-NC 4.0 (confirmado por email por Junwen Wang, autor de correspondencia, '
    '2026-07-29) -- uso no comercial unicamente.'
)

# Pesos SI vienen incluidos en el repo clonado (.h5 por tipo de PTM, ~19MB
# c/u, confirmado en PTM-Prediction/src/engines/deepptmpred_engine.py
# docstring) -- a diferencia de DeepMVP, no hay descarga de modelo aparte.
#
# El checkpoint ESM-2 (esm2_t33_650M_UR50D.pt, 2.6GB) SI es manual: aunque
# 'fair-esm' normalmente permite descargarlo via su propio codigo
# (dl.fbaipublicfiles.com), PTM-Prediction/STATUS.md (linea ~185) registra
# que se instalo manualmente en esta misma organizacion -- se mantiene el
# mismo patron aqui en vez de automatizar una descarga nunca antes
# verificada en un 'scipion3 installb' real. Debe venir acompanado de
# 'esm2_t33_650M_UR50D-contact-regression.pt' (companero obligatorio, ver
# docstring de 'scripts/deepptmpred_runner.py::_extract_esm_features') en el
# MISMO directorio.
ESM_CHECKPOINT_FILENAME = 'esm2_t33_650M_UR50D.pt'
ESM_CONTACT_REGRESSION_FILENAME = 'esm2_t33_650M_UR50D-contact-regression.pt'
ESM_DOWNLOAD_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt'
)
ESM_CONTACT_REGRESSION_URL = (
    'https://dl.fbaipublicfiles.com/fair-esm/regression/'
    'esm2_t33_650M_UR50D-contact-regression.pt'
)

# PyRosetta: licencia academica gratuita (RosettaCommons), wheel NO
# redistribuible ni descargable de forma fiable en este entorno (STATUS.md
# linea ~194-205: los mirrors por defecto del instalador fallaron real y
# reproduciblemente -- 404/TLS -- en esta maquina). Instalacion 100% manual,
# mismo patron que NETMHCPAN_HOME en el proyecto 1: el usuario descarga el
# wheel el mismo (https://www.pyrosetta.org/downloads, requiere cuenta
# academica gratuita) e instala con 'pip install <wheel>' DENTRO del
# entorno conda de este plugin.
PYROSETTA_DOWNLOAD_URL = 'https://www.pyrosetta.org/downloads'

# 17 tipos de PTM que DeepPTMPred predice (un modelo .h5 por tipo, una
# invocacion del runner por tipo) -- verificados contra
# PTM-Prediction/src/config/settings.py::DEEPPTMPRED_PTM_TYPES, que a su vez
# cita la lista real de 'choices' del runner (linea ~237-243).
PTM_TYPES = (
    'phosphorylation', 'acetylation', 'ubiquitination', 'hydroxylation',
    'gamma_carboxyglutamic_acid', 'lys_methylation', 'malonylation',
    'arg_methylation', 'crotonylation', 'succinylation', 'glutathionylation',
    'sumoylation', 's_nitrosylation', 'glutarylation', 'citrullination',
    'o_linked_glycosylation', 'n_linked_glycosylation',
)

# Umbrales calibrados por tipo (verificados contra
# PTM-Prediction/src/config/settings.py::DEEPPTMPRED_CALIBRATED_THRESHOLDS,
# ya validados end-to-end en el pipeline standalone -- ver STATUS.md
# "Calibracion real de DeepPTMPred"). Fallback generico 0.5 si un tipo
# futuro no tiene calibracion propia.
CALIBRATED_THRESHOLDS = {
    'acetylation': 0.6350621,
    'arg_methylation': 0.34068727,
    'citrullination': 0.36854228,
    'crotonylation': 0.86312497,
    'gamma_carboxyglutamic_acid': 0.24807824,
    'glutarylation': 0.4747097,
    'glutathionylation': 0.466462,
    'hydroxylation': 0.35899624,
    'lys_methylation': 0.43064716,
    'malonylation': 0.41699925,
    'n_linked_glycosylation': 0.99802846,
    'o_linked_glycosylation': 0.2619363,
    'phosphorylation': 0.24020174,
    's_nitrosylation': 0.5140331,
    'succinylation': 0.50403893,
    'sumoylation': 0.37326753,
    'ubiquitination': 0.5321394,
}
DEFAULT_MIN_PROBABILITY = 0.5

NOINSTALL_WARNING = (
    "DeepPTMPred no esta instalado correctamente. Revisa que el repo se haya clonado "
    "(DEEPPTMPRED_HOME), que el checkpoint ESM-2 (junto con su companero "
    "'-contact-regression.pt') este en DEEPPTMPRED_ESM_CHECKPOINT, y que PyRosetta este "
    "instalado en el entorno conda del plugin (descarga manual, cuenta academica gratuita "
    f"en {PYROSETTA_DOWNLOAD_URL}). Ver README.rst - Instalacion."
)
