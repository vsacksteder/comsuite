from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import unittest
import os

import numpy as np
from pymatgen.analysis.elasticity.elastic import * 
from pymatgen.analysis.elasticity.strain import Strain, IndependentStrain, Deformation
from pymatgen.analysis.elasticity.stress import Stress
from pymatgen.util.testing import PymatgenTest
from scipy.misc import central_diff_weights
import warnings
import json
import random
from six.moves import zip

test_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                        'test_files')


class ElasticTensorTest(PymatgenTest):
    def setUp(self):
        self.voigt_1 = [[59.33, 28.08, 28.08, 0, 0, 0],
                        [28.08, 59.31, 28.07, 0, 0, 0],
                        [28.08, 28.07, 59.32, 0, 0, 0],
                        [0, 0, 0, 26.35, 0, 0],
                        [0, 0, 0, 0, 26.35, 0],
                        [0, 0, 0, 0, 0, 26.35]]
        mat = np.random.randn(6, 6)
        mat = mat + np.transpose(mat)
        self.rand_elastic_tensor = ElasticTensor.from_voigt(mat)
        self.ft = np.array([[[[59.33, 0, 0],
                              [0, 28.08, 0],
                              [0, 0, 28.08]],
                             [[0, 26.35, 0],
                              [26.35, 0, 0],
                              [0, 0, 0]],
                             [[0, 0, 26.35],
                              [0, 0, 0],
                              [26.35, 0, 0]]],
                            [[[0, 26.35, 0],
                              [26.35, 0, 0],
                              [0, 0, 0]],
                             [[28.08, 0, 0],
                              [0, 59.31, 0],
                              [0, 0, 28.07]],
                             [[0, 0, 0],
                              [0, 0, 26.35],
                              [0, 26.35, 0]]],
                            [[[0, 0, 26.35],
                              [0, 0, 0],
                              [26.35, 0, 0]],
                             [[0, 0, 0],
                              [0, 0, 26.35],
                              [0, 26.35, 0]],
                             [[28.08, 0, 0],
                              [0, 28.07, 0],
                              [0, 0, 59.32]]]])

        self.elastic_tensor_1 = ElasticTensor(self.ft)
        filepath = os.path.join(test_dir, 'Sn_def_stress.json')
        with open(filepath) as f:
            self.def_stress_dict = json.load(f)
        self.structure = self.get_structure("Sn")

        warnings.simplefilter("always")

    def test_properties(self):
        # compliance tensor
        self.assertArrayAlmostEqual(np.linalg.inv(self.elastic_tensor_1.voigt),
                                    self.elastic_tensor_1.compliance_tensor)
        # KG average properties
        self.assertAlmostEqual(38.49111111111, self.elastic_tensor_1.k_voigt)
        self.assertAlmostEqual(22.05866666666, self.elastic_tensor_1.g_voigt)
        self.assertAlmostEqual(38.49110945133, self.elastic_tensor_1.k_reuss)
        self.assertAlmostEqual(20.67146635306, self.elastic_tensor_1.g_reuss)
        self.assertAlmostEqual(38.49111028122, self.elastic_tensor_1.k_vrh)
        self.assertAlmostEqual(21.36506650986, self.elastic_tensor_1.g_vrh)
        
        # universal anisotropy
        self.assertAlmostEqual(0.33553509658699,
                               self.elastic_tensor_1.universal_anisotropy)
        # homogeneous poisson
        self.assertAlmostEqual(0.26579965576472,
                               self.elastic_tensor_1.homogeneous_poisson)
        # voigt notation tensor
        self.assertArrayAlmostEqual(self.elastic_tensor_1.voigt,
                                    self.voigt_1)
        # young's modulus
        self.assertAlmostEqual(54087787667.160583,
                               self.elastic_tensor_1.y_mod)

        # prop dict
        prop_dict = self.elastic_tensor_1.property_dict
        self.assertAlmostEqual(prop_dict["homogeneous_poisson"], 0.26579965576)
        for k, v in prop_dict.items():
            self.assertAlmostEqual(getattr(self.elastic_tensor_1, k), v)

    def test_structure_based_methods(self):
        # trans_velocity
        self.assertAlmostEqual(1996.35019877,
                               self.elastic_tensor_1.trans_v(self.structure))

        # long_velocity
        self.assertAlmostEqual(3534.68123832,
                               self.elastic_tensor_1.long_v(self.structure))
        # Snyder properties
        self.assertAlmostEqual(18.06127074,
                               self.elastic_tensor_1.snyder_ac(self.structure))
        self.assertAlmostEqual(0.18937465,
                               self.elastic_tensor_1.snyder_opt(self.structure))
        self.assertAlmostEqual(18.25064540,
                               self.elastic_tensor_1.snyder_total(self.structure))
        # Clarke
        self.assertAlmostEqual(0.3450307,
                               self.elastic_tensor_1.clarke_thermalcond(self.structure))
        # Cahill
        self.assertAlmostEqual(0.37896275,
                               self.elastic_tensor_1.cahill_thermalcond(self.structure))
        # Debye
        self.assertAlmostEqual(247.3058931,
                               self.elastic_tensor_1.debye_temperature(self.structure))
        self.assertAlmostEqual(189.05670205,
                               self.elastic_tensor_1.debye_temperature_gibbs(self.structure))

        # structure-property dict
        sprop_dict = self.elastic_tensor_1.get_structure_property_dict(self.structure)
        self.assertAlmostEqual(sprop_dict["long_v"], 3534.68123832)
        for k, v in sprop_dict.items():
            if k=="structure":
                self.assertEqual(v, self.structure)
            else:
                f = getattr(self.elastic_tensor_1, k)
                if callable(f):
                    self.assertAlmostEqual(getattr(self.elastic_tensor_1, k)(self.structure), v)
                else:
                    self.assertAlmostEqual(getattr(self.elastic_tensor_1, k), v)

    def test_new(self):
        self.assertArrayAlmostEqual(self.elastic_tensor_1,
                                    ElasticTensor(self.ft))
        nonsymm = self.ft
        nonsymm[0, 1, 2, 2] += 1.0
        with warnings.catch_warnings(record=True) as w:
            ElasticTensor(nonsymm)
            self.assertEqual(len(w), 1)
        badtensor1 = np.zeros((3, 3, 3))
        badtensor2 = np.zeros((3, 3, 3, 2))
        self.assertRaises(ValueError, ElasticTensor, badtensor1)
        self.assertRaises(ValueError, ElasticTensor, badtensor2)

    def test_from_pseudoinverse(self):
        strain_list = [Strain.from_deformation(def_matrix)
                       for def_matrix in self.def_stress_dict['deformations']]
        stress_list = [stress for stress in self.def_stress_dict['stresses']]
        with warnings.catch_warnings(record=True):
            et_fl = -0.1*ElasticTensor.from_pseudoinverse(strain_list, 
                                                          stress_list).voigt
            self.assertArrayAlmostEqual(et_fl.round(2),
                                        [[59.29, 24.36, 22.46, 0, 0, 0],
                                         [28.06, 56.91, 22.46, 0, 0, 0],
                                         [28.06, 25.98, 54.67, 0, 0, 0],
                                         [0, 0, 0, 26.35, 0, 0],
                                         [0, 0, 0, 0, 26.35, 0],
                                         [0, 0, 0, 0, 0, 26.35]])

    def test_from_stress_dict(self):
        stress_dict = dict(list(zip([IndependentStrain(def_matrix) for def_matrix
                                in self.def_stress_dict['deformations']],
                                [Stress(stress_matrix) for stress_matrix
                                in self.def_stress_dict['stresses']])))
        minimal_sd = {k:v for k, v in stress_dict.items() 
                      if (abs(k[k.ij] - 0.015) < 1e-10
                      or  abs(k[k.ij] - 0.01005) < 1e-10)}
        with warnings.catch_warnings(record = True):
            et_from_sd = ElasticTensor.from_stress_dict(stress_dict)
            et_from_minimal_sd = ElasticTensor.from_stress_dict(minimal_sd)
        self.assertArrayAlmostEqual(et_from_sd.voigt_symmetrized.round(2),
                                    self.elastic_tensor_1)
        self.assertAlmostEqual(50.63394169, et_from_minimal_sd[0,0,0,0])

    def test_energy_density(self):

        film_elac = ElasticTensor.from_voigt([
            [324.32,  187.3,   170.92,    0.,      0.,      0.],
            [187.3,   324.32,  170.92,    0.,      0.,      0.],
            [170.92,  170.92,  408.41,    0.,      0.,      0.],
            [0.,      0.,      0.,    150.73,    0.,      0.],
            [0.,      0.,      0.,      0.,    150.73,    0.],
            [0.,      0.,      0.,      0.,      0.,    238.74]])

        dfm = Deformation([[ -9.86004855e-01,2.27539582e-01,-4.64426035e-17],
                           [ -2.47802121e-01,-9.91208483e-01,-7.58675185e-17],
                           [ -6.12323400e-17,-6.12323400e-17,1.00000000e+00]])

        self.assertAlmostEqual(film_elac.energy_density(dfm.green_lagrange_strain),
            0.000125664672793)

        film_elac.energy_density(Strain.from_deformation([[ 0.99774738,  0.11520994, -0.        ],
                                        [-0.11520994,  0.99774738,  0.        ],
                                        [-0.,         -0.,          1.,        ]]))


class ElasticTensorExpansionTest(PymatgenTest):
    def setUp(self):
        with open(os.path.join(test_dir, 'test_toec_data.json')) as f:
            self.data_dict = json.load(f)
        self.strains = [Strain(sm) for sm in self.data_dict['strains']]
        self.pk_stresses = [Stress(d) for d in self.data_dict['pk_stresses']]
        self.c2 = self.data_dict["C2_raw"]
        self.c3 = self.data_dict["C3_raw"]
        self.exp = ElasticTensorExpansion.from_voigt([self.c2, self.c3])

    def test_init(self):
        cijkl = Tensor.from_voigt(self.c2)
        cijklmn = Tensor.from_voigt(self.c3)
        exp = ElasticTensorExpansion([cijkl, cijklmn])
        from_voigt = ElasticTensorExpansion.from_voigt([self.c2, self.c3])
        self.assertEqual(exp.order, 3)

    def test_from_diff_fit(self):
        exp = ElasticTensorExpansion.from_diff_fit(self.strains, self.pk_stresses)

    def test_calculate_stress(self):
        calc_stress = self.exp.calculate_stress(self.strains[0])
        self.assertArrayAlmostEqual(self.pk_stresses[0], calc_stress, decimal=2)

    def test_energy_density(self):
        self.exp.energy_density(self.strains[0])


class NthOrderElasticTensorTest(PymatgenTest):
    def setUp(self):
        with open(os.path.join(test_dir, 'test_toec_data.json')) as f:
            self.data_dict = json.load(f)
        self.strains = [Strain(sm) for sm in self.data_dict['strains']]
        self.pk_stresses = [Stress(d) for d in self.data_dict['pk_stresses']]
        self.c2 = NthOrderElasticTensor.from_voigt(self.data_dict["C2_raw"])
        self.c3 = NthOrderElasticTensor.from_voigt(self.data_dict["C3_raw"])
        
    def test_init(self):
        c2 = NthOrderElasticTensor(self.c2.tolist())
        c3 = NthOrderElasticTensor(self.c3.tolist())
        c4 = NthOrderElasticTensor(np.zeros([3]*8))
        for n, c in enumerate([c2, c3, c4]):
            self.assertEqual(c.order, n+2)
        self.assertRaises(ValueError, NthOrderElasticTensor, np.zeros([3]*5))

    def test_from_diff_fit(self):
        c3 = NthOrderElasticTensor.from_diff_fit(self.strains, self.pk_stresses, 
                                                 eq_stress = self.data_dict["eq_stress"], 
                                                 order=3)
        self.assertArrayAlmostEqual(c3.voigt, self.data_dict["C3_raw"], decimal=2)

    def test_calculate_stress(self):
        calc_stress = self.c2.calculate_stress(self.strains[0])
        self.assertArrayAlmostEqual(self.pk_stresses[0], calc_stress, decimal=0)
        # Test calculation from voigt strain
        calc_stress_voigt = self.c2.calculate_stress(self.strains[0].voigt)

    def test_energy_density(self):
        self.c3.energy_density(self.strains[0])


class DiffFitTest(PymatgenTest):
    """
    Tests various functions related to diff fitting
    """
    def setUp(self):
        with open(os.path.join(test_dir, 'test_toec_data.json')) as f:
            self.data_dict = json.load(f)
        self.strains = [Strain(sm) for sm in self.data_dict['strains']]
        self.pk_stresses = [Stress(d) for d in self.data_dict['pk_stresses']]

    def test_get_strain_state_dict(self):
        strain_inds = [(0,), (1,), (2,), (1, 3), (1, 2, 3)]
        vecs = {}
        strain_states = []
        for strain_ind in strain_inds:
            ss = np.zeros(6)
            np.put(ss, strain_ind, 1)
            strain_states.append(tuple(ss))
            vec = np.zeros((4, 6))
            rand_values = np.random.uniform(0.1, 1, 4)
            for i in strain_ind:
                vec[:, i] = rand_values
            vecs[strain_ind] = vec
        all_strains = [Strain.from_voigt(v).zeroed() for vec in vecs.values()
                       for v in vec]
        random.shuffle(all_strains)
        all_stresses = [Stress.from_voigt(np.random.random(6)).zeroed()
                        for s in all_strains]
        strain_dict = {k.tostring():v for k,v in zip(all_strains, all_stresses)}
        ss_dict = get_strain_state_dict(all_strains, all_stresses, add_eq=False)
        # Check length of ss_dict
        self.assertEqual(len(strain_inds), len(ss_dict))
        # Check sets of strain states are correct
        self.assertEqual(set(strain_states), set(ss_dict.keys()))
        for strain_state, data in ss_dict.items():
            # Check correspondence of strains/stresses
            for strain, stress in zip(data["strains"], data["stresses"]):
                self.assertArrayAlmostEqual(Stress.from_voigt(stress), 
                                            strain_dict[Strain.from_voigt(strain).tostring()])

    def test_find_eq_stress(self):
        random_strains = [Strain.from_voigt(s) for s in np.random.uniform(0.1, 1, (20, 6))]
        random_stresses = [Strain.from_voigt(s) for s in np.random.uniform(0.1, 1, (20, 6))]
        with warnings.catch_warnings(record=True):
            no_eq = find_eq_stress(random_strains, random_stresses)
            self.assertArrayAlmostEqual(no_eq, np.zeros((3,3)))
        random_strains[12] = Strain.from_voigt(np.zeros(6))
        eq_stress = find_eq_stress(random_strains, random_stresses)
        self.assertArrayAlmostEqual(random_stresses[12], eq_stress)

    def test_get_diff_coeff(self):
        forward_11 = get_diff_coeff([0, 1], 1)
        forward_13 = get_diff_coeff([0, 1, 2, 3], 1)
        backward_26 = get_diff_coeff(np.arange(-6, 1), 2)
        central_29 = get_diff_coeff(np.arange(-4, 5), 2)
        self.assertArrayAlmostEqual(forward_11, [-1, 1])
        self.assertArrayAlmostEqual(forward_13, [-11./6, 3, -3./2, 1./3])
        self.assertArrayAlmostEqual(backward_26, [137./180, -27./5,33./2,-254./9,
                                                  117./4,-87./5,203./45])
        self.assertArrayAlmostEqual(central_29, central_diff_weights(9, 2))

    def test_generate_pseudo(self):
        strain_states = np.eye(6).tolist()
        m2, abs = generate_pseudo(strain_states, order=2)
        m3, abs = generate_pseudo(strain_states, order=3)

    def test_fit(self):
        cdf = diff_fit(self.strains, self.pk_stresses,
                               self.data_dict["eq_stress"])
        reduced = [(e, pk) for e, pk in zip(self.strains, self.pk_stresses)
                   if not (abs(abs(e)-0.05)<1e-10).any()]
        # Get reduced dataset
        r_strains, r_pk_stresses = zip(*reduced)
        with warnings.catch_warnings(record=True):
            c2 = diff_fit(r_strains, r_pk_stresses,
                                  self.data_dict["eq_stress"], order=2) 
            c2, c3, c4 = diff_fit(r_strains, r_pk_stresses,
                                          self.data_dict["eq_stress"], 
                                          order=4) 
            c2, c3 = diff_fit(self.strains, self.pk_stresses,
                                      self.data_dict["eq_stress"], order=3) 
            c2_red, c3_red = diff_fit(r_strains, r_pk_stresses,
                                              self.data_dict["eq_stress"], 
                                              order=3)
            self.assertArrayAlmostEqual(c2.voigt, self.data_dict["C2_raw"])
            self.assertArrayAlmostEqual(c3.voigt, self.data_dict["C3_raw"], decimal=5)
            self.assertArrayAlmostEqual(c2, c2_red, decimal=0)
            self.assertArrayAlmostEqual(c3, c3_red, decimal=-1)

if __name__ == '__main__':
    unittest.main()
