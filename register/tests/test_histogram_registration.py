#!/usr/bin/env python

import numpy as np
from nibabel import Nifti1Image

from ..affine import Affine, Rigid
from ..histogram_registration import HistogramRegistration
from .._register import _joint_histogram

from numpy.testing import (assert_array_equal,
                           assert_equal,
                           assert_almost_equal,
                           assert_raises)

dummy_affine = np.eye(4)


def make_data_bool(dx=100, dy=100, dz=50):
    return (np.random.rand(dx, dy, dz)
                   - np.random.rand()) > 0


def make_data_uint8(dx=100, dy=100, dz=50):
    return (256 * (np.random.rand(dx, dy, dz)
                   - np.random.rand())).astype('uint8')


def make_data_int16(dx=100, dy=100, dz=50):
    return (256 * (np.random.rand(dx, dy, dz)
                   - np.random.rand())).astype('int16')


def make_data_float64(dx=100, dy=100, dz=50):
    return (256 * (np.random.rand(dx, dy, dz)
                 - np.random.rand())).astype('float64')


def _test_clamping(I, thI=0.0, clI=256, mask=None):
    R = HistogramRegistration(I, I, bins=clI,
                              from_mask=mask, to_mask=mask,
                              spacing=[1, 1, 1])
    Ic = R._from_data
    Ic2 = R._to_data[1:-1, 1:-1, 1:-1]
    assert_equal(Ic, Ic2)
    dyn = Ic.max() + 1
    assert_equal(dyn, R._joint_hist.shape[0])
    assert_equal(dyn, R._joint_hist.shape[1])
    return Ic, Ic2


def test_clamping_uint8():
    I = Nifti1Image(make_data_uint8(), dummy_affine)
    _test_clamping(I)


def test_clamping_uint8_nonstd():
    I = Nifti1Image(make_data_uint8(), dummy_affine)
    _test_clamping(I, 10, 165)


def test_clamping_int16():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    _test_clamping(I)


def test_masked_clamping_int16():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    _test_clamping(I, mask=make_data_bool())


def test_clamping_int16_nonstd():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    _test_clamping(I, 10, 165)


def test_clamping_float64():
    I = Nifti1Image(make_data_float64(), dummy_affine)
    _test_clamping(I)


def test_clamping_float64_nonstd():
    I = Nifti1Image(make_data_float64(), dummy_affine)
    _test_clamping(I, 10, 165)


def _test_similarity_measure(simi, val):
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(I.get_data().copy(), dummy_affine)
    R = HistogramRegistration(I, J, spacing=[2, 1, 3])
    R.similarity = simi
    assert_almost_equal(R.eval(Affine()), val)


def _test_renormalization(simi, simi2ll):
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(make_data_int16(), dummy_affine)
    R = HistogramRegistration(I, J, similarity=simi, spacing=[2, 1, 3])
    def_s = simi2ll(R.eval(Affine()))
    R._set_similarity(simi, renormalize='ml')
    assert_almost_equal(R.eval(Affine()), def_s)
    R._set_similarity(simi, renormalize='nml')
    assert_almost_equal(R.eval(Affine()), def_s)


def test_correlation_coefficient():
    _test_similarity_measure('cc', 1.0)


def test_correlation_ratio():
    _test_similarity_measure('cr', 1.0)


def test_correlation_ratio_L1():
    _test_similarity_measure('crl1', 1.0)


def test_normalized_mutual_information():
    _test_similarity_measure('nmi', 2.0)


def test_renormalized_correlation_coefficient():
    simi2ll = lambda x: -.5 * np.log(1 - x)
    _test_renormalization('cc', simi2ll)


def test_renormalized_correlation_ratio():
    simi2ll = lambda x: -.5 * np.log(1 - x)
    _test_renormalization('cr', simi2ll)


def test_renormalized_correlation_ratio_l1():
    simi2ll = lambda x: -np.log(1 - x)
    _test_renormalization('crl1', simi2ll)


def test_renormalized_mutual_information():
    simi2ll = lambda x: x
    _test_renormalization('mi', simi2ll)


def test_joint_hist_eval():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(I.get_data().copy(), dummy_affine)
    # Obviously the data should be the same
    assert_array_equal(I.get_data(), J.get_data())
    # Instantiate default thing
    R = HistogramRegistration(I, J, spacing=[1, 1, 1])
    R.similarity = 'cc'
    null_affine = Affine()
    val = R.eval(null_affine)
    assert_almost_equal(val, 1.0)
    # Try with what should be identity
    assert_array_equal(R._from_data.shape, I.shape)


def test_joint_hist_raw():
    # Set up call to joint histogram
    jh_arr = np.zeros((10, 10), dtype=np.double)
    data_shape = (2, 3, 4)
    data = np.random.randint(size=data_shape,
                             low=0, high=10).astype(np.short)
    data2 = np.zeros(np.array(data_shape) + 2, dtype=np.short)
    data2[:] = -1
    data2[1:-1, 1:-1, 1:-1] = data.copy()
    vox_coords = np.indices(data_shape).transpose((1, 2, 3, 0))
    vox_coords = np.ascontiguousarray(vox_coords.astype(np.double))
    _joint_histogram(jh_arr, data.flat, data2, vox_coords, 0)
    assert_almost_equal(np.diag(np.diag(jh_arr)), jh_arr)


def test_explore():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(make_data_int16(), dummy_affine)
    R = HistogramRegistration(I, J)
    T = Affine()
    simi, params = R.explore(T, (0, [-1, 0, 1]), (1, [-1, 0, 1]))


def test_histogram_registration():
    """ Test the histogram registration class.
    """
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(I.get_data().copy(), dummy_affine)
    assert_raises(ValueError, HistogramRegistration,
                  I, J, spacing=[0, 1, 3])


def test_set_fov():
    I = Nifti1Image(make_data_int16(), dummy_affine)
    J = Nifti1Image(I.get_data().copy(), dummy_affine)
    R = HistogramRegistration(I, J)
    R.set_fov(npoints=np.prod(I.shape))
    assert_equal(R._from_data.shape, I.shape)
    half_shape = tuple([I.shape[i] / 2 for i in range(3)])
    R.set_fov(spacing=(2, 2, 2))
    assert_equal(R._from_data.shape, half_shape)
    R.set_fov(corner=half_shape)
    assert_equal(R._from_data.shape, half_shape)
    R.set_fov(size=half_shape)
    assert_equal(R._from_data.shape, half_shape)


def test_histogram_masked_registration():
    """ Test the histogram registration class.
    """
    I = Nifti1Image(make_data_int16(dx=100, dy=100, dz=50),
                    dummy_affine)
    J = Nifti1Image(make_data_int16(dx=100, dy=100, dz=50),
                    dummy_affine)
    mask = (np.zeros((100, 100, 50)) == 1)
    mask[10:20, 10:20, 10:20] = True
    R = HistogramRegistration(I, J, to_mask=mask, from_mask=mask)
    sim1 = R.eval(Affine())
    I = Nifti1Image(I.get_data()[mask].reshape(10, 10, 10),
                    dummy_affine)
    J = Nifti1Image(J.get_data()[mask].reshape(10, 10, 10),
                    dummy_affine)
    R = HistogramRegistration(I, J)
    sim2 = R.eval(Affine())
    assert_equal(sim1, sim2)


def test_similarity_derivatives():
    """ Test gradient and Hessian computation of the registration
    objective function.
    """
    I = Nifti1Image(make_data_int16(dx=100, dy=100, dz=50),
                    dummy_affine)
    J = Nifti1Image(np.ones((100, 100, 50), dtype='int16'),
                    dummy_affine)
    R = HistogramRegistration(I, J)
    T = Rigid()
    g = R.eval_gradient(T)
    assert_equal(g.dtype, float)
    assert_equal(g, np.zeros(6))
    H = R.eval_hessian(T)
    assert_equal(H.dtype, float)
    assert_equal(H, np.zeros((6, 6)))


def test_smoothing():
    """ Test smoothing the `to` image.
    """
    I = Nifti1Image(make_data_int16(dx=100, dy=100, dz=50),
                    dummy_affine)
    T = Rigid()
    R = HistogramRegistration(I, I)
    R1 = HistogramRegistration(I, I, sigma=(0,1))
    s = R.eval(T)
    s1 = R1.eval(T)
    assert_almost_equal(s, 1)
    assert s1 < s
    assert_raises(ValueError, HistogramRegistration, I, I, sigma=-1)


if __name__ == "__main__":
    import nose
    nose.run(argv=['', __file__])
