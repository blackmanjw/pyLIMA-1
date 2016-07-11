# -*- coding: utf-8 -*-
"""
Created on Thu May 19 15:08:11 2016

@author: ebachelet
"""
import collections

import mock
import numpy as np
import pytest

from pyLIMA import microlmodels


def _create_event():
    event = mock.MagicMock()
    event.telescopes = [mock.MagicMock()]
    event.telescopes[0].name = 'Test'
    event.telescopes[0].lightcurve_flux = np.array([[0, 1, 1], [42, 6, 6]])
    event.telescopes[0].gamma = 0.5
    return event


def test_create_PSPL_model():

    event = _create_event()
    pspl_model = microlmodels.create_model('PSPL', event)

    assert isinstance(pspl_model, microlmodels.ModelPSPL)


def test_create_FSPL_model():
    
    event = _create_event()
    fspl_model = microlmodels.create_model('FSPL', event)

    assert isinstance(fspl_model, microlmodels.ModelFSPL)


def test_create_bad_model():
    # Both tests are equivalent
    event = _create_event()
    # Using a context manager
    with pytest.raises(microlmodels.ModelException) as model_exception:
        microlmodels.create_model('BAD', event)
    assert 'Unknown model "BAD"' in str(model_exception)

    # Manually checking for an exception and error message
    try:
        microlmodels.create_model('BAD', event)
        pytest.fail()
    except microlmodels.ModelException as model_exception:
        assert 'Unknown model "BAD"' in str(model_exception)




def test_define_parameters_model_dictionnary():
    event = _create_event()

    Model = microlmodels.create_model('FSPL', event)

    assert Model.model_dictionnary.keys() == ['to', 'uo', 'tE', 'rho', 'fs_Test', 'g_Test']
    assert Model.model_dictionnary.values() == [0, 1, 2, 3, 4, 5]


def test_define_parameters_boundaries():
    event = _create_event()

    Model = microlmodels.create_model('FSPL', event)

    assert Model.parameters_boundaries == [(-300, 342), (-2.0, 2.0), (1.0, 300), (1e-5, 0.05)]


def test_magnification_FSPL_computation():
    event = _create_event()

    Model = microlmodels.create_model('FSPL', event)
    Parameters = collections.namedtuple('parameters', ['to', 'uo', 'tE', 'rho'])
    parameters = Parameters(0, 0.1, 1, 5e-2)

    amplification, impact_parameter = Model.model_magnification(event.telescopes[0], parameters)

    assert np.allclose(amplification, np.array([ 10.34817883,   1.00000064]))
    assert np.allclose(impact_parameter, np.array([0.1, 42.0]))

def test_magnification_PSPL_computation():
    event = _create_event()

    Model = microlmodels.create_model('PSPL', event)
    Parameters = collections.namedtuple('parameters', ['to', 'uo', 'tE'])
    parameters = Parameters(0, 0.1, 1)

    amplification, impact_parameter = Model.model_magnification(event.telescopes[0], parameters)
    assert np.allclose(amplification,np.array([10.03746101, 1.00]))
    assert np.allclose(impact_parameter, np.array([0.1, 42.0]))


def test_PSPL_computate_microlensing_model():
    event = _create_event()

    Model = microlmodels.create_model('PSPL', event)
    Parameters = collections.namedtuple('parameters', ['to', 'uo', 'tE', 'fs_Test', 'g_Test'])
    parameters = Parameters(0, 0.1, 1, 10, 1)

    model, _ = Model.compute_the_microlensing_model(event.telescopes[0], parameters)
    assert np.allclose(model, np.array([10*(10.03746101+1), 10*(1.00+1)]))


def test_FSPL_computate_microlensing_model():
    event = _create_event()

    Model = microlmodels.create_model('FSPL', event)
    Parameters = collections.namedtuple('parameters', ['to', 'uo', 'tE', 'rho', 'fs_Test',
                                                       'g_Test'])
    parameters = Parameters(0, 0.1, 1, 5e-2, 10, 1)

    model, _ = Model.compute_the_microlensing_model(event.telescopes[0], parameters)
    assert np.allclose(model, np.array([10*(10.34817832+1), 10*(1.00+1)]))

def test_no_fancy_parameters_to_pyLIMA_standard_parameters():

    event = _create_event()
    Model = microlmodels.create_model('PSPL', event)
    parameters = [42, 51]
    fancy = Model.fancy_parameters_to_pyLIMA_standard_parameters(parameters)
    
    assert parameters == fancy


def test_one_fancy_parameters_to_pyLIMA_standard_parameters():

    event = _create_event()
    Model = microlmodels.create_model('FSPL', event)
 
    Model.fancy_to_pyLIMA_dictionnary = {'logrho': 'rho'}
    Model.pyLIMA_to_fancy = {'logrho': lambda parameters: np.log10(parameters.rho)}
    Model.fancy_to_pyLIMA = {'rho': lambda parameters: 10 ** parameters.logrho}
    Model.define_model_parameters()
 

    Parameters  = [0.28, 0.1, 35.6, -1.30102]
    pyLIMA_parameters = Model.compute_pyLIMA_parameters(Parameters)
    
    assert pyLIMA_parameters.to == 0.28
    assert pyLIMA_parameters.uo == 0.1	
    assert pyLIMA_parameters.tE == 35.6
    assert pyLIMA_parameters.logrho == -1.30102
    assert np.allclose(pyLIMA_parameters.rho, 0.05, rtol=0.001, atol=0.001)

def test_mixing_fancy_parameters_to_pyLIMA_standard_parameters():

    event = _create_event()
    Model = microlmodels.create_model('FSPL', event)
 
    Model.fancy_to_pyLIMA_dictionnary = {'tstar':'tE','logrho': 'rho'}
    Model.pyLIMA_to_fancy = {'logrho': lambda parameters: np.log10(parameters.rho),
                             'tstar':lambda parameters:(parameters.uo*parameters.tE)}
    Model.fancy_to_pyLIMA = {'rho': lambda parameters: 10 ** parameters.logrho,
                             'tE':lambda parameters: (parameters.tstar/parameters.uo)}
    Model.define_model_parameters()
 
    tE = 35.6
    uo = 0.1

    Parameters  = [0.28, uo, uo*tE, -1.30102]
    pyLIMA_parameters = Model.compute_pyLIMA_parameters(Parameters)
    
    assert pyLIMA_parameters.to == 0.28
    assert pyLIMA_parameters.uo == uo	
    assert pyLIMA_parameters.tE == tE
    assert pyLIMA_parameters.tstar == uo*tE
    assert pyLIMA_parameters.logrho == -1.30102
    assert np.allclose(pyLIMA_parameters.rho, 0.05, rtol=0.001, atol=0.001)


def test_complicated_mixing_fancy_parameters_to_pyLIMA_standard_parameters():

    event = _create_event()
    Model = microlmodels.create_model('FSPL', event)
 
    Model.fancy_to_pyLIMA_dictionnary = {'tstar':'tE','logrho': 'rho'}
    Model.pyLIMA_to_fancy = {'logrho': lambda parameters: np.log10(parameters.rho),
                             'tstar':lambda parameters:(parameters.logrho*parameters.tE)}
    Model.fancy_to_pyLIMA = {'rho': lambda parameters: 10 ** parameters.logrho,
                             'tE':lambda parameters: (parameters.tstar/parameters.logrho)}
    Model.define_model_parameters()
 
    tE = 35.6
    uo = 0.1
    logrho = -1.30102
    Parameters  = [0.28, uo, tE*logrho, logrho]
    pyLIMA_parameters = Model.compute_pyLIMA_parameters(Parameters)
    
    assert pyLIMA_parameters.to == 0.28
    assert pyLIMA_parameters.uo == uo	
    assert pyLIMA_parameters.tE == tE
    assert pyLIMA_parameters.tstar == np.log10(pyLIMA_parameters.rho)*tE
    assert pyLIMA_parameters.logrho == logrho
    assert np.allclose(pyLIMA_parameters.rho, 0.05, rtol=0.001, atol=0.001)



def test_compute_parallax():

    #NEED TO DO PARALLAX FIRST
    return

def test_compute_parallax_curvature():

    #NEED TO DO PARALLAX FIRST
    return
