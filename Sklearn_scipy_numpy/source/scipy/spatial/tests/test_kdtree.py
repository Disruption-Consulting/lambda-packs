# Copyright Anne M. Archibald 2008
# Released under the scipy license

from __future__ import division, print_function, absolute_import

from numpy.testing import (assert_equal, assert_array_equal,
    assert_almost_equal, assert_array_almost_equal, assert_, run_module_suite)

import numpy as np
from scipy.spatial import KDTree, Rectangle, distance_matrix, cKDTree
from scipy.spatial.ckdtree import cKDTreeNode
from scipy.spatial import minkowski_distance

def distance_box(a, b, p, boxsize):
    diff = a - b
    diff[diff > 0.5 * boxsize] -= boxsize
    diff[diff < -0.5 * boxsize] += boxsize
    d = minkowski_distance(diff, 0, p)
    return d

class ConsistencyTests:
    def distance(self, a, b, p):
        return minkowski_distance(a, b, p)

    def test_nearest(self):
        x = self.x
        d, i = self.kdtree.query(x, 1)
        assert_almost_equal(d**2,np.sum((x-self.data[i])**2))
        eps = 1e-8
        assert_(np.all(np.sum((self.data-x[np.newaxis,:])**2,axis=1) > d**2-eps))

    def test_m_nearest(self):
        x = self.x
        m = self.m
        dd, ii = self.kdtree.query(x, m)
        d = np.amax(dd)
        i = ii[np.argmax(dd)]
        assert_almost_equal(d**2,np.sum((x-self.data[i])**2))
        eps = 1e-8
        assert_equal(np.sum(np.sum((self.data-x[np.newaxis,:])**2,axis=1) < d**2+eps),m)

    def test_points_near(self):
        x = self.x
        d = self.d
        dd, ii = self.kdtree.query(x, k=self.kdtree.n, distance_upper_bound=d)
        eps = 1e-8
        hits = 0
        for near_d, near_i in zip(dd,ii):
            if near_d == np.inf:
                continue
            hits += 1
            assert_almost_equal(near_d**2,np.sum((x-self.data[near_i])**2))
            assert_(near_d < d+eps, "near_d=%g should be less than %g" % (near_d,d))
        assert_equal(np.sum(self.distance(self.data,x,2) < d**2+eps),hits)

    def test_points_near_l1(self):
        x = self.x
        d = self.d
        dd, ii = self.kdtree.query(x, k=self.kdtree.n, p=1, distance_upper_bound=d)
        eps = 1e-8
        hits = 0
        for near_d, near_i in zip(dd,ii):
            if near_d == np.inf:
                continue
            hits += 1
            assert_almost_equal(near_d,self.distance(x,self.data[near_i],1))
            assert_(near_d < d+eps, "near_d=%g should be less than %g" % (near_d,d))
        assert_equal(np.sum(self.distance(self.data,x,1) < d+eps),hits)

    def test_points_near_linf(self):
        x = self.x
        d = self.d
        dd, ii = self.kdtree.query(x, k=self.kdtree.n, p=np.inf, distance_upper_bound=d)
        eps = 1e-8
        hits = 0
        for near_d, near_i in zip(dd,ii):
            if near_d == np.inf:
                continue
            hits += 1
            assert_almost_equal(near_d,self.distance(x,self.data[near_i],np.inf))
            assert_(near_d < d+eps, "near_d=%g should be less than %g" % (near_d,d))
        assert_equal(np.sum(self.distance(self.data,x,np.inf) < d+eps),hits)

    def test_approx(self):
        x = self.x
        k = self.k
        eps = 0.1
        d_real, i_real = self.kdtree.query(x, k)
        d, i = self.kdtree.query(x, k, eps=eps)
        assert_(np.all(d <= d_real*(1+eps)))


class test_random(ConsistencyTests):
    def setUp(self):
        self.n = 100
        self.m = 4
        np.random.seed(1234)
        self.data = np.random.randn(self.n, self.m)
        self.kdtree = KDTree(self.data,leafsize=2)
        self.x = np.random.randn(self.m)
        self.d = 0.2
        self.k = 10


class test_random_far(test_random):
    def setUp(self):
        test_random.setUp(self)
        self.x = np.random.randn(self.m)+10


class test_small(ConsistencyTests):
    def setUp(self):
        self.data = np.array([[0,0,0],
                              [0,0,1],
                              [0,1,0],
                              [0,1,1],
                              [1,0,0],
                              [1,0,1],
                              [1,1,0],
                              [1,1,1]])
        self.kdtree = KDTree(self.data)
        self.n = self.kdtree.n
        self.m = self.kdtree.m
        np.random.seed(1234)
        self.x = np.random.randn(3)
        self.d = 0.5
        self.k = 4

    def test_nearest(self):
        assert_array_equal(
                self.kdtree.query((0,0,0.1), 1),
                (0.1,0))

    def test_nearest_two(self):
        assert_array_equal(
                self.kdtree.query((0,0,0.1), 2),
                ([0.1,0.9],[0,1]))


class test_small_nonleaf(test_small):
    def setUp(self):
        test_small.setUp(self)
        self.kdtree = KDTree(self.data,leafsize=1)


class test_small_compiled(test_small):
    def setUp(self):
        test_small.setUp(self)
        self.kdtree = cKDTree(self.data)


class test_small_nonleaf_compiled(test_small):
    def setUp(self):
        test_small.setUp(self)
        self.kdtree = cKDTree(self.data,leafsize=1)


class test_random_compiled(test_random):
    def setUp(self):
        test_random.setUp(self)
        self.kdtree = cKDTree(self.data)


class test_random_far_compiled(test_random_far):
    def setUp(self):
        test_random_far.setUp(self)
        self.kdtree = cKDTree(self.data)


class test_vectorization:
    def setUp(self):
        self.data = np.array([[0,0,0],
                              [0,0,1],
                              [0,1,0],
                              [0,1,1],
                              [1,0,0],
                              [1,0,1],
                              [1,1,0],
                              [1,1,1]])
        self.kdtree = KDTree(self.data)

    def test_single_query(self):
        d, i = self.kdtree.query(np.array([0,0,0]))
        assert_(isinstance(d,float))
        assert_(np.issubdtype(i, int))

    def test_vectorized_query(self):
        d, i = self.kdtree.query(np.zeros((2,4,3)))
        assert_equal(np.shape(d),(2,4))
        assert_equal(np.shape(i),(2,4))

    def test_single_query_multiple_neighbors(self):
        s = 23
        kk = self.kdtree.n+s
        d, i = self.kdtree.query(np.array([0,0,0]),k=kk)
        assert_equal(np.shape(d),(kk,))
        assert_equal(np.shape(i),(kk,))
        assert_(np.all(~np.isfinite(d[-s:])))
        assert_(np.all(i[-s:] == self.kdtree.n))

    def test_vectorized_query_multiple_neighbors(self):
        s = 23
        kk = self.kdtree.n+s
        d, i = self.kdtree.query(np.zeros((2,4,3)),k=kk)
        assert_equal(np.shape(d),(2,4,kk))
        assert_equal(np.shape(i),(2,4,kk))
        assert_(np.all(~np.isfinite(d[:,:,-s:])))
        assert_(np.all(i[:,:,-s:] == self.kdtree.n))

    def test_single_query_all_neighbors(self):
        d, i = self.kdtree.query([0,0,0],k=None,distance_upper_bound=1.1)
        assert_(isinstance(d,list))
        assert_(isinstance(i,list))

    def test_vectorized_query_all_neighbors(self):
        d, i = self.kdtree.query(np.zeros((2,4,3)),k=None,distance_upper_bound=1.1)
        assert_equal(np.shape(d),(2,4))
        assert_equal(np.shape(i),(2,4))

        assert_(isinstance(d[0,0],list))
        assert_(isinstance(i[0,0],list))


class test_vectorization_compiled:
    def setUp(self):
        self.data = np.array([[0,0,0],
                              [0,0,1],
                              [0,1,0],
                              [0,1,1],
                              [1,0,0],
                              [1,0,1],
                              [1,1,0],
                              [1,1,1]])
        self.kdtree = cKDTree(self.data)

    def test_single_query(self):
        d, i = self.kdtree.query([0,0,0])
        assert_(isinstance(d,float))
        assert_(isinstance(i,int))

    def test_vectorized_query(self):
        d, i = self.kdtree.query(np.zeros((2,4,3)))
        assert_equal(np.shape(d),(2,4))
        assert_equal(np.shape(i),(2,4))

    def test_vectorized_query_noncontiguous_values(self):
        np.random.seed(1234)
        qs = np.random.randn(3,1000).T
        ds, i_s = self.kdtree.query(qs)
        for q, d, i in zip(qs,ds,i_s):
            assert_equal(self.kdtree.query(q),(d,i))

    def test_single_query_multiple_neighbors(self):
        s = 23
        kk = self.kdtree.n+s
        d, i = self.kdtree.query([0,0,0],k=kk)
        assert_equal(np.shape(d),(kk,))
        assert_equal(np.shape(i),(kk,))
        assert_(np.all(~np.isfinite(d[-s:])))
        assert_(np.all(i[-s:] == self.kdtree.n))

    def test_vectorized_query_multiple_neighbors(self):
        s = 23
        kk = self.kdtree.n+s
        d, i = self.kdtree.query(np.zeros((2,4,3)),k=kk)
        assert_equal(np.shape(d),(2,4,kk))
        assert_equal(np.shape(i),(2,4,kk))
        assert_(np.all(~np.isfinite(d[:,:,-s:])))
        assert_(np.all(i[:,:,-s:] == self.kdtree.n))


class ball_consistency:
    def distance(self, a, b, p):
        return minkowski_distance(a, b, p)

    def test_in_ball(self):
        l = self.T.query_ball_point(self.x, self.d, p=self.p, eps=self.eps)
        for i in l:
            assert_(self.distance(self.data[i],self.x,self.p) <= self.d*(1.+self.eps))

    def test_found_all(self):
        c = np.ones(self.T.n,dtype=bool)
        l = self.T.query_ball_point(self.x, self.d, p=self.p, eps=self.eps)
        c[l] = False
        assert_(np.all(self.distance(self.data[c],self.x,self.p) >= self.d/(1.+self.eps)))


class test_random_ball(ball_consistency):

    def setUp(self):
        n = 100
        m = 4
        np.random.seed(1234)
        self.data = np.random.randn(n,m)
        self.T = KDTree(self.data,leafsize=2)
        self.x = np.random.randn(m)
        self.p = 2.
        self.eps = 0
        self.d = 0.2


class test_random_ball_compiled(ball_consistency):

    def setUp(self):
        n = 100
        m = 4
        np.random.seed(1234)
        self.data = np.random.randn(n,m)
        self.T = cKDTree(self.data,leafsize=2)
        self.x = np.random.randn(m)
        self.p = 2.
        self.eps = 0
        self.d = 0.2

class test_random_ball_compiled_periodic(ball_consistency):
    def distance(self, a, b, p):
        return distance_box(a, b, p, 1.0)

    def setUp(self):
        n = 100
        m = 4
        np.random.seed(1234)
        self.data = np.random.uniform(size=(n,m))
        self.T = cKDTree(self.data,leafsize=2, boxsize=1)
        self.x = np.ones(m) * 0.1
        self.p = 2.
        self.eps = 0
        self.d = 0.2

    def test_in_ball_outside(self):
        l = self.T.query_ball_point(self.x + 1.0, self.d, p=self.p, eps=self.eps)
        for i in l:
            assert_(self.distance(self.data[i],self.x,self.p) <= self.d*(1.+self.eps))
        l = self.T.query_ball_point(self.x - 1.0, self.d, p=self.p, eps=self.eps)
        for i in l:
            assert_(self.distance(self.data[i],self.x,self.p) <= self.d*(1.+self.eps))

    def test_found_all_outside(self):
        c = np.ones(self.T.n,dtype=bool)
        l = self.T.query_ball_point(self.x + 1.0, self.d, p=self.p, eps=self.eps)
        c[l] = False
        assert_(np.all(self.distance(self.data[c],self.x,self.p) >= self.d/(1.+self.eps)))

        l = self.T.query_ball_point(self.x - 1.0, self.d, p=self.p, eps=self.eps)
        c[l] = False
        assert_(np.all(self.distance(self.data[c],self.x,self.p) >= self.d/(1.+self.eps)))

class test_random_ball_approx(test_random_ball):

    def setUp(self):
        test_random_ball.setUp(self)
        self.eps = 0.1


class test_random_ball_approx_compiled(test_random_ball_compiled):

    def setUp(self):
        test_random_ball_compiled.setUp(self)
        self.eps = 0.1

class test_random_ball_approx_compiled_periodic(test_random_ball_compiled_periodic):

    def setUp(self):
        test_random_ball_compiled_periodic.setUp(self)
        self.eps = 0.1


class test_random_ball_far(test_random_ball):

    def setUp(self):
        test_random_ball.setUp(self)
        self.d = 2.


class test_random_ball_far_compiled(test_random_ball_compiled):

    def setUp(self):
        test_random_ball_compiled.setUp(self)
        self.d = 2.

class test_random_ball_far_compiled_periodic(test_random_ball_compiled_periodic):

    def setUp(self):
        test_random_ball_compiled_periodic.setUp(self)
        self.d = 2.


class test_random_ball_l1(test_random_ball):

    def setUp(self):
        test_random_ball.setUp(self)
        self.p = 1


class test_random_ball_l1_compiled(test_random_ball_compiled):

    def setUp(self):
        test_random_ball_compiled.setUp(self)
        self.p = 1

class test_random_ball_l1_compiled_periodic(test_random_ball_compiled_periodic):

    def setUp(self):
        test_random_ball_compiled_periodic.setUp(self)
        self.p = 1


class test_random_ball_linf(test_random_ball):

    def setUp(self):
        test_random_ball.setUp(self)
        self.p = np.inf

class test_random_ball_linf_compiled_periodic(test_random_ball_compiled_periodic):

    def setUp(self):
        test_random_ball_compiled_periodic.setUp(self)
        self.p = np.inf


def test_random_ball_vectorized():

    n = 20
    m = 5
    T = KDTree(np.random.randn(n,m))

    r = T.query_ball_point(np.random.randn(2,3,m),1)
    assert_equal(r.shape,(2,3))
    assert_(isinstance(r[0,0],list))


def test_random_ball_vectorized_compiled():

    n = 20
    m = 5
    np.random.seed(1234)
    T = cKDTree(np.random.randn(n,m))

    r = T.query_ball_point(np.random.randn(2,3,m),1)
    assert_equal(r.shape,(2,3))
    assert_(isinstance(r[0,0],list))
    
    
def test_query_ball_point_multithreading():
    np.random.seed(0)
    n = 5000
    k = 2
    points = np.random.randn(n,k)
    T = cKDTree(points)
    l1 = T.query_ball_point(points,0.003,n_jobs=1)
    l2 = T.query_ball_point(points,0.003,n_jobs=64)
    l3 = T.query_ball_point(points,0.003,n_jobs=-1)
    
    for i in range(n):
        if l1[i] or l2[i]:
            assert_array_equal(l1[i],l2[i])
        
    for i in range(n):
        if l1[i] or l3[i]:
            assert_array_equal(l1[i],l3[i])
         

class two_trees_consistency:

    def distance(self, a, b, p):
        return minkowski_distance(a, b, p)

    def test_all_in_ball(self):
        r = self.T1.query_ball_tree(self.T2, self.d, p=self.p, eps=self.eps)
        for i, l in enumerate(r):
            for j in l:
                assert_(self.distance(self.data1[i],self.data2[j],self.p) <= self.d*(1.+self.eps))

    def test_found_all(self):
        r = self.T1.query_ball_tree(self.T2, self.d, p=self.p, eps=self.eps)
        for i, l in enumerate(r):
            c = np.ones(self.T2.n,dtype=bool)
            c[l] = False
            assert_(np.all(self.distance(self.data2[c],self.data1[i],self.p) >= self.d/(1.+self.eps)))


class test_two_random_trees(two_trees_consistency):

    def setUp(self):
        n = 50
        m = 4
        np.random.seed(1234)
        self.data1 = np.random.randn(n,m)
        self.T1 = KDTree(self.data1,leafsize=2)
        self.data2 = np.random.randn(n,m)
        self.T2 = KDTree(self.data2,leafsize=2)
        self.p = 2.
        self.eps = 0
        self.d = 0.2


class test_two_random_trees_compiled(two_trees_consistency):

    def setUp(self):
        n = 50
        m = 4
        np.random.seed(1234)
        self.data1 = np.random.randn(n,m)
        self.T1 = cKDTree(self.data1,leafsize=2)
        self.data2 = np.random.randn(n,m)
        self.T2 = cKDTree(self.data2,leafsize=2)
        self.p = 2.
        self.eps = 0
        self.d = 0.2

class test_two_random_trees_compiled_periodic(two_trees_consistency):
    def distance(self, a, b, p):
        return distance_box(a, b, p, 1.0)

    def setUp(self):
        n = 50
        m = 4
        np.random.seed(1234)
        self.data1 = np.random.uniform(size=(n,m))
        self.T1 = cKDTree(self.data1,leafsize=2, boxsize=1.0)
        self.data2 = np.random.uniform(size=(n,m))
        self.T2 = cKDTree(self.data2,leafsize=2, boxsize=1.0)
        self.p = 2.
        self.eps = 0
        self.d = 0.2

class test_two_random_trees_far(test_two_random_trees):

    def setUp(self):
        test_two_random_trees.setUp(self)
        self.d = 2


class test_two_random_trees_far_compiled(test_two_random_trees_compiled):

    def setUp(self):
        test_two_random_trees_compiled.setUp(self)
        self.d = 2

class test_two_random_trees_far_compiled_periodic(test_two_random_trees_compiled_periodic):

    def setUp(self):
        test_two_random_trees_compiled_periodic.setUp(self)
        self.d = 2


class test_two_random_trees_linf(test_two_random_trees):

    def setUp(self):
        test_two_random_trees.setUp(self)
        self.p = np.inf


class test_two_random_trees_linf_compiled(test_two_random_trees_compiled):

    def setUp(self):
        test_two_random_trees_compiled.setUp(self)
        self.p = np.inf

class test_two_random_trees_linf_compiled_periodic(test_two_random_trees_compiled_periodic):

    def setUp(self):
        test_two_random_trees_compiled_periodic.setUp(self)
        self.p = np.inf


class test_rectangle:

    def setUp(self):
        self.rect = Rectangle([0,0],[1,1])

    def test_min_inside(self):
        assert_almost_equal(self.rect.min_distance_point([0.5,0.5]),0)

    def test_min_one_side(self):
        assert_almost_equal(self.rect.min_distance_point([0.5,1.5]),0.5)

    def test_min_two_sides(self):
        assert_almost_equal(self.rect.min_distance_point([2,2]),np.sqrt(2))

    def test_max_inside(self):
        assert_almost_equal(self.rect.max_distance_point([0.5,0.5]),1/np.sqrt(2))

    def test_max_one_side(self):
        assert_almost_equal(self.rect.max_distance_point([0.5,1.5]),np.hypot(0.5,1.5))

    def test_max_two_sides(self):
        assert_almost_equal(self.rect.max_distance_point([2,2]),2*np.sqrt(2))

    def test_split(self):
        less, greater = self.rect.split(0,0.1)
        assert_array_equal(less.maxes,[0.1,1])
        assert_array_equal(less.mins,[0,0])
        assert_array_equal(greater.maxes,[1,1])
        assert_array_equal(greater.mins,[0.1,0])


def test_distance_l2():
    assert_almost_equal(minkowski_distance([0,0],[1,1],2),np.sqrt(2))


def test_distance_l1():
    assert_almost_equal(minkowski_distance([0,0],[1,1],1),2)


def test_distance_linf():
    assert_almost_equal(minkowski_distance([0,0],[1,1],np.inf),1)


def test_distance_vectorization():
    np.random.seed(1234)
    x = np.random.randn(10,1,3)
    y = np.random.randn(1,7,3)
    assert_equal(minkowski_distance(x,y).shape,(10,7))


class count_neighbors_consistency:
    def test_one_radius(self):
        r = 0.2
        assert_equal(self.T1.count_neighbors(self.T2, r),
                np.sum([len(l) for l in self.T1.query_ball_tree(self.T2,r)]))

    def test_large_radius(self):
        r = 1000
        assert_equal(self.T1.count_neighbors(self.T2, r),
                np.sum([len(l) for l in self.T1.query_ball_tree(self.T2,r)]))

    def test_multiple_radius(self):
        rs = np.exp(np.linspace(np.log(0.01),np.log(10),3))
        results = self.T1.count_neighbors(self.T2, rs)
        assert_(np.all(np.diff(results) >= 0))
        for r,result in zip(rs, results):
            assert_equal(self.T1.count_neighbors(self.T2, r), result)

class test_count_neighbors(count_neighbors_consistency):

    def setUp(self):
        n = 50
        m = 2
        np.random.seed(1234)
        self.T1 = KDTree(np.random.randn(n,m),leafsize=2)
        self.T2 = KDTree(np.random.randn(n,m),leafsize=2)


class test_count_neighbors_compiled(count_neighbors_consistency):

    def setUp(self):
        n = 50
        m = 2
        np.random.seed(1234)
        self.T1 = cKDTree(np.random.randn(n,m),leafsize=2)
        self.T2 = cKDTree(np.random.randn(n,m),leafsize=2)


class sparse_distance_matrix_consistency:

    def distance(self, a, b, p):
        return minkowski_distance(a, b, p)

    def test_consistency_with_neighbors(self):
        M = self.T1.sparse_distance_matrix(self.T2, self.r)
        r = self.T1.query_ball_tree(self.T2, self.r)
        for i,l in enumerate(r):
            for j in l:
                assert_almost_equal(M[i,j],
                                    self.distance(self.T1.data[i], self.T2.data[j], self.p),
                                    decimal=14)
        for ((i,j),d) in M.items():
            assert_(j in r[i])

    def test_zero_distance(self):
        # raises an exception for bug 870 (FIXME: Does it?)
        self.T1.sparse_distance_matrix(self.T1, self.r)

class test_sparse_distance_matrix(sparse_distance_matrix_consistency):

    def setUp(self):
        n = 50
        m = 4
        np.random.seed(1234)
        data1 = np.random.randn(n,m)
        data2 = np.random.randn(n,m)
        self.T1 = cKDTree(data1,leafsize=2)
        self.T2 = cKDTree(data2,leafsize=2)
        self.r = 0.5
        self.p = 2
        self.data1 = data1
        self.data2 = data2
        self.n = n
        self.m = m

class test_sparse_distance_matrix_compiled(sparse_distance_matrix_consistency):

    def setUp(self):
        n = 50
        m = 4
        np.random.seed(0)
        data1 = np.random.randn(n,m)
        data2 = np.random.randn(n,m)
        self.T1 = cKDTree(data1,leafsize=2)
        self.T2 = cKDTree(data2,leafsize=2)
        self.ref_T1 = KDTree(data1, leafsize=2)
        self.ref_T2 = KDTree(data2, leafsize=2)
        self.r = 0.5
        self.n = n
        self.m = m
        self.data1 = data1
        self.data2 = data2
        self.p = 2

    def test_consistency_with_python(self):
        M1 = self.T1.sparse_distance_matrix(self.T2, self.r)
        M2 = self.ref_T1.sparse_distance_matrix(self.ref_T2, self.r)
        assert_array_almost_equal(M1.todense(), M2.todense(), decimal=14)
        
    def test_against_logic_error_regression(self):
        # regression test for gh-5077 logic error
        np.random.seed(0)
        too_many = np.array(np.random.randn(18, 2), dtype=int)
        tree = cKDTree(too_many, balanced_tree=False, compact_nodes=False)
        d = tree.sparse_distance_matrix(tree, 3).todense()
        assert_array_almost_equal(d, d.T, decimal=14)

    def test_ckdtree_return_types(self):
        # brute-force reference
        ref = np.zeros((self.n,self.n))
        for i in range(self.n):
            for j in range(self.n):
                v = self.data1[i,:] - self.data2[j,:]
                ref[i,j] = np.dot(v,v)
        ref = np.sqrt(ref)    
        ref[ref > self.r] = 0.
        # test return type 'dict'
        dist = np.zeros((self.n,self.n))
        r = self.T1.sparse_distance_matrix(self.T2, self.r, output_type='dict')
        for i,j in r.keys():
            dist[i,j] = r[(i,j)]
        assert_array_almost_equal(ref, dist, decimal=14)
        # test return type 'ndarray'
        dist = np.zeros((self.n,self.n))
        r = self.T1.sparse_distance_matrix(self.T2, self.r, 
            output_type='ndarray')
        for k in range(r.shape[0]):
            i = r['i'][k]
            j = r['j'][k]
            v = r['v'][k]
            dist[i,j] = v
        assert_array_almost_equal(ref, dist, decimal=14)
        # test return type 'dok_matrix'
        r = self.T1.sparse_distance_matrix(self.T2, self.r, 
            output_type='dok_matrix')
        assert_array_almost_equal(ref, r.todense(), decimal=14)
        # test return type 'coo_matrix'
        r = self.T1.sparse_distance_matrix(self.T2, self.r, 
            output_type='coo_matrix')
        assert_array_almost_equal(ref, r.todense(), decimal=14)


def test_distance_matrix():
    m = 10
    n = 11
    k = 4
    np.random.seed(1234)
    xs = np.random.randn(m,k)
    ys = np.random.randn(n,k)
    ds = distance_matrix(xs,ys)
    assert_equal(ds.shape, (m,n))
    for i in range(m):
        for j in range(n):
            assert_almost_equal(minkowski_distance(xs[i],ys[j]),ds[i,j])


def test_distance_matrix_looping():
    m = 10
    n = 11
    k = 4
    np.random.seed(1234)
    xs = np.random.randn(m,k)
    ys = np.random.randn(n,k)
    ds = distance_matrix(xs,ys)
    dsl = distance_matrix(xs,ys,threshold=1)
    assert_equal(ds,dsl)


def check_onetree_query(T,d):
    r = T.query_ball_tree(T, d)
    s = set()
    for i, l in enumerate(r):
        for j in l:
            if i < j:
                s.add((i,j))

    assert_(s == T.query_pairs(d))

def test_onetree_query():
    np.random.seed(0)
    n = 50
    k = 4
    points = np.random.randn(n,k)
    T = KDTree(points)
    yield check_onetree_query, T, 0.1

    points = np.random.randn(3*n,k)
    points[:n] *= 0.001
    points[n:2*n] += 2
    T = KDTree(points)
    yield check_onetree_query, T, 0.1
    yield check_onetree_query, T, 0.001
    yield check_onetree_query, T, 0.00001
    yield check_onetree_query, T, 1e-6


def test_onetree_query_compiled():
    np.random.seed(0)
    n = 100
    k = 4
    points = np.random.randn(n,k)
    T = cKDTree(points)
    yield check_onetree_query, T, 0.1

    points = np.random.randn(3*n,k)
    points[:n] *= 0.001
    points[n:2*n] += 2
    T = cKDTree(points)
    yield check_onetree_query, T, 0.1
    yield check_onetree_query, T, 0.001
    yield check_onetree_query, T, 0.00001
    yield check_onetree_query, T, 1e-6


def test_query_pairs_single_node():
    tree = KDTree([[0, 1]])
    assert_equal(tree.query_pairs(0.5), set())


def test_query_pairs_single_node_compiled():
    tree = cKDTree([[0, 1]])
    assert_equal(tree.query_pairs(0.5), set())


def test_ckdtree_query_pairs():
    np.random.seed(0)
    n = 50
    k = 2
    r = 0.1
    r2 = r**2
    points = np.random.randn(n,k)
    T = cKDTree(points)
    # brute force reference
    brute = set()
    for i in range(n):
        for j in range(i+1,n):
            v = points[i,:] - points[j,:]
            if np.dot(v,v) <= r2:
                brute.add((i,j))
    l0 = sorted(brute)
    # test default return type
    s = T.query_pairs(r)
    l1 = sorted(s)    
    assert_array_equal(l0,l1)
    # test return type 'set'
    s = T.query_pairs(r, output_type='set')
    l1 = sorted(s)    
    assert_array_equal(l0,l1)
    # test return type 'ndarray'
    s = set()
    arr = T.query_pairs(r, output_type='ndarray')
    for i in range(arr.shape[0]):
        s.add((int(arr[i,0]),int(arr[i,1])))
    l2 = sorted(s)
    assert_array_equal(l0,l2)
    
    
def test_ball_point_ints():
    # Regression test for #1373.
    x, y = np.mgrid[0:4, 0:4]
    points = list(zip(x.ravel(), y.ravel()))
    tree = KDTree(points)
    assert_equal(sorted([4, 8, 9, 12]),
                 sorted(tree.query_ball_point((2, 0), 1)))
    points = np.asarray(points, dtype=float)
    tree = KDTree(points)
    assert_equal(sorted([4, 8, 9, 12]),
                 sorted(tree.query_ball_point((2, 0), 1)))


def test_kdtree_comparisons():
    # Regression test: node comparisons were done wrong in 0.12 w/Py3.
    nodes = [KDTree.node() for _ in range(3)]
    assert_equal(sorted(nodes), sorted(nodes[::-1]))


def test_ckdtree_build_modes():
    # check if different build modes for cKDTree give
    # similar query results
    np.random.seed(0)
    n = 5000
    k = 4
    points = np.random.randn(n, k)
    T1 = cKDTree(points).query(points, k=5)[-1]
    T2 = cKDTree(points, compact_nodes=False).query(points, k=5)[-1]
    T3 = cKDTree(points, balanced_tree=False).query(points, k=5)[-1]
    T4 = cKDTree(points, compact_nodes=False, balanced_tree=False).query(points, k=5)[-1]
    assert_array_equal(T1, T2)
    assert_array_equal(T1, T3)
    assert_array_equal(T1, T4)

def test_ckdtree_pickle():
    # test if it is possible to pickle
    # a cKDTree
    try:
        import cPickle as pickle
    except ImportError:
        import pickle
    np.random.seed(0)
    n = 50
    k = 4
    points = np.random.randn(n, k)
    T1 = cKDTree(points)
    tmp = pickle.dumps(T1)
    T2 = pickle.loads(tmp)
    T1 = T1.query(points, k=5)[-1]
    T2 = T2.query(points, k=5)[-1]
    assert_array_equal(T1, T2)

def test_ckdtree_pickle_boxsize():
    # test if it is possible to pickle a periodic
    # cKDTree
    try:
        import cPickle as pickle
    except ImportError:
        import pickle
    np.random.seed(0)
    n = 50
    k = 4
    points = np.random.uniform(size=(n, k))
    T1 = cKDTree(points, boxsize=1.0)
    tmp = pickle.dumps(T1)
    T2 = pickle.loads(tmp)
    T1 = T1.query(points, k=5)[-1]
    T2 = T2.query(points, k=5)[-1]
    assert_array_equal(T1, T2)
    
def test_ckdtree_copy_data():
    # check if copy_data=True makes the kd-tree
    # impervious to data corruption by modification of 
    # the data arrray
    np.random.seed(0)
    n = 5000
    k = 4
    points = np.random.randn(n, k)
    T = cKDTree(points, copy_data=True)
    q = points.copy()
    T1 = T.query(q, k=5)[-1]
    points[...] = np.random.randn(n, k)
    T2 = T.query(q, k=5)[-1]
    assert_array_equal(T1, T2)
    
def test_ckdtree_parallel():
    # check if parallel=True also generates correct
    # query results
    np.random.seed(0)
    n = 5000
    k = 4
    points = np.random.randn(n, k)
    T = cKDTree(points)
    T1 = T.query(points, k=5, n_jobs=64)[-1]
    T2 = T.query(points, k=5, n_jobs=-1)[-1]
    T3 = T.query(points, k=5)[-1]
    assert_array_equal(T1, T2)
    assert_array_equal(T1, T3)

def test_ckdtree_view():        
    # Check that the nodes can be correctly viewed from Python.
    # This test also sanity checks each node in the cKDTree, and
    # thus verifies the internal structure of the kd-tree.
    np.random.seed(0)
    n = 100
    k = 4
    points = np.random.randn(n, k)
    kdtree = cKDTree(points)
    
    # walk the whole kd-tree and sanity check each node
    def recurse_tree(n):
        assert_(isinstance(n, cKDTreeNode)) 
        if n.split_dim == -1: 
            assert_(n.lesser is None)
            assert_(n.greater is None)
            assert_(n.indices.shape[0] <= kdtree.leafsize)
        else:
            recurse_tree(n.lesser)
            recurse_tree(n.greater)
            x = n.lesser.data_points[:, n.split_dim]
            y = n.greater.data_points[:, n.split_dim]
            assert_(x.max() < y.min())
    
    recurse_tree(kdtree.tree)
    # check that indices are correctly retreived
    n = kdtree.tree
    assert_array_equal(np.sort(n.indices), range(100))
    # check that data_points are correctly retreived
    assert_array_equal(kdtree.data[n.indices, :], n.data_points)

# cKDTree is specialized to type double points, so no need to make
# a unit test corresponding to test_ball_point_ints()

def test_ckdtree_box():
    # check ckdtree periodic boundary
    n = 2000
    m = 2
    k = 3
    np.random.seed(1234)
    data = np.random.uniform(size=(n, m))
    kdtree = cKDTree(data, leafsize=1, boxsize=1.0)

    # use the standard python KDTree for the simulated periodic box
    kdtree2 = cKDTree(data, leafsize=1)

    dd, ii = kdtree.query(data, k)

    dd1, ii1 = kdtree.query(data + 1.0, k)
    assert_almost_equal(dd, dd1)
    assert_equal(ii, ii1)
    
    dd1, ii1 = kdtree.query(data - 1.0, k)
    assert_almost_equal(dd, dd1)
    assert_equal(ii, ii1)

    dd2, ii2 = simulate_periodic_box(kdtree2, data, k, boxsize=1.0)
    assert_almost_equal(dd, dd2)
    assert_equal(ii, ii2)

def test_ckdtree_box_upper_bounds():
    data = np.linspace(0, 2, 10).reshape(-1, 1)
    try:
        cKDTree(data, leafsize=1, boxsize=1.0)
    except ValueError:
        return
    raise AssertionError("ValueError is not raised")

def test_ckdtree_box_lower_bounds():
    data = np.linspace(-1, 1, 10)
    try:
        cKDTree(data, leafsize=1, boxsize=1.0)
    except ValueError:
        return
    raise AssertionError("ValueError is not raised")

def simulate_periodic_box(kdtree, data, k, boxsize):
    dd = []
    ii = []
    x = np.arange(3 ** data.shape[1])
    nn = np.array(np.unravel_index(x, [3] * data.shape[1])).T
    nn = nn - 1.0
    for n in nn:
        image = data + n * 1.0 * boxsize
        dd2, ii2 = kdtree.query(image, k)
        dd2 = dd2.reshape(-1, k)
        ii2 = ii2.reshape(-1, k)
        dd.append(dd2)
        ii.append(ii2)
    dd = np.concatenate(dd, axis=-1)
    ii = np.concatenate(ii, axis=-1)

    result = np.empty([len(data), len(nn) * k], dtype=[
            ('ii', 'i8'),
            ('dd', 'f8')])
    result['ii'][:] = ii
    result['dd'][:] = dd
    result.sort(order='dd')
    return result['dd'][:, :k], result['ii'][:,:k]
    
def test_ckdtree_memuse():
    # unit test adaptation of gh-5630
    try:
        import resource
    except ImportError:
        # resource is not available on Windows with Python 2.6
        return
    # Make some data
    dx, dy = 0.05, 0.05
    y, x = np.mgrid[slice(1, 5 + dy, dy),
                    slice(1, 5 + dx, dx)]
    z = np.sin(x)**10 + np.cos(10 + y*x) * np.cos(x)
    z_copy = np.empty_like(z)
    z_copy[:] = z
    # Place FILLVAL in z_copy at random number of random locations
    FILLVAL = 99.
    mask = np.random.random_integers(0, z.size - 1, np.random.randint(50) + 5)
    z_copy.flat[mask] = FILLVAL
    igood = np.vstack(np.where(x != FILLVAL)).T
    ibad = np.vstack(np.where(x == FILLVAL)).T
    mem_use = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # burn-in
    for i in range(10):
        tree = cKDTree(igood)
    # count memleaks while constructing and querying cKDTree
    num_leaks = 0
    for i in range(100):
        mem_use = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        tree = cKDTree(igood)
        dist, iquery = tree.query(ibad, k=4, p=2)
        new_mem_use = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if new_mem_use > mem_use:
            num_leaks += 1
    # ideally zero leaks, but errors might accidentally happen
    # outside cKDTree
    assert_(num_leaks < 10)
    
if __name__ == "__main__":
    run_module_suite()