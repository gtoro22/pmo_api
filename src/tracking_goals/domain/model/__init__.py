"""Modelo de dominio del servicio de objetivos."""

from tracking_goals.domain.model.evaluacion import Evaluacion
from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.objetivo import Objetivo
from tracking_goals.domain.model.perspectiva import Perspectiva
from tracking_goals.domain.model.registro_plano import RegistroPlano
from tracking_goals.domain.model.resultado_consulta import ESTADO_OK, ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario

__all__ = [
    "ESTADO_OK",
    "Evaluacion",
    "Metadatos",
    "Objetivo",
    "Perspectiva",
    "RegistroPlano",
    "ResultadoConsulta",
    "Usuario",
]
