# Copyright (c) DIRECT Contributors

"""Tests for SSL/JSSL engines in direct.nn.vsharp.vsharp_engine module."""

import functools

import numpy as np
import pytest
import torch

from direct.config.defaults import DefaultConfig, FunctionConfig, LossConfig, TrainingConfig, ValidationConfig
from direct.data.transforms import fft2, ifft2
from direct.nn.vsharp.config import VSharpNet3DConfig, VSharpNetConfig
from direct.nn.vsharp.vsharp import VSharpNet, VSharpNet3D
from direct.nn.vsharp.vsharp_engine import VSharpNetJSSLEngine, VSharpNetSSLEngine


def create_sample(**kwargs):
    sample = dict()
    for k, v in locals()["kwargs"].items():
        sample[k] = v
    return sample


@pytest.mark.parametrize(
    "shape",
    [(4, 3, 10, 16, 2), (5, 1, 10, 12, 2)],
)
@pytest.mark.parametrize(
    "loss_fns",
    [["l1_loss", "kspace_nmse_loss", "kspace_nmae_loss"]],
)
@pytest.mark.parametrize(
    "num_steps, num_steps_dc_gd, num_filters, num_pool_layers",
    [[4, 2, 10, 2]],
)
@pytest.mark.parametrize(
    "normalized",
    [True, False],
)
def test_vsharpnet_ssl_engine(shape, loss_fns, num_steps, num_steps_dc_gd, num_filters, num_pool_layers, normalized):
    # Operators
    forward_operator = functools.partial(fft2, centered=True)
    backward_operator = functools.partial(ifft2, centered=True)
    # Configs
    loss_config = LossConfig(losses=[FunctionConfig(loss) for loss in loss_fns])
    training_config = TrainingConfig(loss=loss_config)
    validation_config = ValidationConfig(crop=None)
    model_config = VSharpNetConfig(
        num_steps=num_steps,
        num_steps_dc_gd=num_steps_dc_gd,
        image_unet_num_filters=num_filters,
        image_unet_num_pool_layers=num_pool_layers,
        auxiliary_steps=-1,
    )
    config = DefaultConfig(training=training_config, validation=validation_config, model=model_config)
    # Models
    model = VSharpNet(
        forward_operator,
        backward_operator,
        num_steps=model_config.num_steps,
        num_steps_dc_gd=model_config.num_steps_dc_gd,
        image_unet_num_filters=model_config.image_unet_num_filters,
        image_unet_num_pool_layers=model_config.image_unet_num_pool_layers,
        auxiliary_steps=model_config.auxiliary_steps,
    )
    sensitivity_model = torch.nn.Conv2d(2, 2, kernel_size=1)
    # Define engine
    engine = VSharpNetSSLEngine(config, model, "cpu", fft2, ifft2, sensitivity_model=sensitivity_model)
    engine.ndim = 2
    # Simulate training
    # Test _do_iteration function with a single data batch
    data = create_sample(
        input_sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        target_sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        input_kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        sensitivity_map=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        target=torch.from_numpy(np.random.randn(shape[0], shape[2], shape[3])).float(),
        scaling_factor=torch.ones(shape[0]),
    )
    loss_fns = engine.build_loss()
    out = engine._do_iteration(data, loss_fns)
    out.output_image.shape == (shape[0],) + tuple(shape[2:-1])

    # Simulate validation
    engine.model.eval()
    # Test _do_iteration function with a single data batch
    data = create_sample(
        sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        masked_kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        sensitivity_map=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        target=torch.from_numpy(np.random.randn(shape[0], shape[2], shape[3])).float(),
        scaling_factor=torch.ones(shape[0]),
    )
    loss_fns = engine.build_loss()
    out = engine._do_iteration(data, loss_fns)
    assert out.output_image.shape == (shape[0],) + tuple(shape[2:-1])


@pytest.mark.parametrize(
    "shape",
    [(4, 3, 10, 16, 2), (5, 1, 10, 12, 2)],
)
@pytest.mark.parametrize(
    "loss_fns",
    [["l1_loss", "kspace_nmse_loss", "kspace_nmae_loss"]],
)
@pytest.mark.parametrize(
    "num_steps, num_steps_dc_gd, num_filters, num_pool_layers",
    [[4, 2, 10, 2]],
)
@pytest.mark.parametrize(
    "normalized",
    [True, False],
)
def test_vsharpnet_jssl_engine(shape, loss_fns, num_steps, num_steps_dc_gd, num_filters, num_pool_layers, normalized):
    # Operators
    forward_operator = functools.partial(fft2, centered=True)
    backward_operator = functools.partial(ifft2, centered=True)
    # Configs
    loss_config = LossConfig(losses=[FunctionConfig(loss) for loss in loss_fns])
    training_config = TrainingConfig(loss=loss_config)
    validation_config = ValidationConfig(crop=None)
    model_config = VSharpNetConfig(
        num_steps=num_steps,
        num_steps_dc_gd=num_steps_dc_gd,
        image_unet_num_filters=num_filters,
        image_unet_num_pool_layers=num_pool_layers,
        auxiliary_steps=-1,
    )
    config = DefaultConfig(training=training_config, validation=validation_config, model=model_config)
    # Models
    model = VSharpNet(
        forward_operator,
        backward_operator,
        num_steps=model_config.num_steps,
        num_steps_dc_gd=model_config.num_steps_dc_gd,
        image_unet_num_filters=model_config.image_unet_num_filters,
        image_unet_num_pool_layers=model_config.image_unet_num_pool_layers,
        auxiliary_steps=model_config.auxiliary_steps,
    )
    sensitivity_model = torch.nn.Conv2d(2, 2, kernel_size=1)
    # Define engine
    engine = VSharpNetJSSLEngine(config, model, "cpu", fft2, ifft2, sensitivity_model=sensitivity_model)
    engine.ndim = 2

    # Simulate training (SSL)
    # Test _do_iteration function with a single data batch
    data = create_sample(
        input_sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        target_sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        input_kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        sensitivity_map=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        target=torch.from_numpy(np.random.randn(shape[0], shape[2], shape[3])).float(),
        scaling_factor=torch.ones(shape[0]),
        is_ssl=torch.ones(shape[0]).bool(),
    )
    loss_fns = engine.build_loss()
    out = engine._do_iteration(data, loss_fns)
    assert out.output_image.shape == (shape[0],) + tuple(shape[2:-1])

    # Simulate training (SL)
    # Test _do_iteration function with a single data batch
    data = create_sample(
        sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        masked_kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        sensitivity_map=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        target=torch.from_numpy(np.random.randn(shape[0], shape[2], shape[3])).float(),
        scaling_factor=torch.ones(shape[0]),
        is_ssl=torch.zeros(shape[0]).bool(),
    )
    loss_fns = engine.build_loss()
    out = engine._do_iteration(data, loss_fns)
    assert out.output_image.shape == (shape[0],) + tuple(shape[2:-1])

    # Simulate validation
    engine.model.eval()
    # Test _do_iteration function with a single data batch
    data = create_sample(
        sampling_mask=torch.from_numpy(np.random.rand(1, 1, shape[2], shape[3], 1)).round().bool(),
        masked_kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        kspace=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        sensitivity_map=torch.from_numpy(np.random.randn(shape[0], shape[1], shape[2], shape[3], 2)).float(),
        target=torch.from_numpy(np.random.randn(shape[0], shape[2], shape[3])).float(),
        scaling_factor=torch.ones(shape[0]),
        is_ssl=torch.zeros(shape[0]).bool(),
    )
    loss_fns = engine.build_loss()
    out = engine._do_iteration(data, loss_fns)
    assert out.output_image.shape == (shape[0],) + tuple(shape[2:-1])
