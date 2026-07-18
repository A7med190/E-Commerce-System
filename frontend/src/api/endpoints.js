import { api } from './client'

export const productsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.set(k, v)
    })
    return api.get(`/products/?${qs.toString()}`)
  },
  detail: (slug) => api.get(`/products/${slug}/`),
  customizations: (slug) => api.get(`/products/${slug}/customizations/`),
  related: (slug) => api.get(`/products/${slug}/related/`),
}

export const categoriesApi = {
  list: (parent) =>
    api.get(parent ? `/categories/?parent=${parent}` : '/categories/'),
  detail: (slug) => api.get(`/categories/${slug}/`),
}

export const authApi = {
  register: (data) => api.post('/auth/register/', data),
  login: (email, password) =>
    api.post('/auth/login/', { email, password }),
  me: () => api.get('/auth/me/'),
  changePassword: (data) => api.post('/auth/change-password/', data),
  addresses: () => api.get('/users/me/addresses/'),
  createAddress: (data) => api.post('/users/me/addresses/', data),
  deleteAddress: (id) => api.delete(`/users/me/addresses/${id}/`),
}

export const cartApi = {
  get: () => api.get('/cart/'),
  clear: () => api.delete('/cart/clear/'),
  addItem: (data) => api.post('/cart/items/', data),
  updateItem: (id, quantity) => api.patch(`/cart/items/${id}/`, { quantity }),
  removeItem: (id) => api.delete(`/cart/items/${id}/`),
}

export const wishlistApi = {
  get: () => api.get('/wishlist/'),
  addItem: (productId) => api.post('/wishlist/items/', { product_id: productId }),
  removeItem: (id) => api.delete(`/wishlist/items/${id}/`),
}

export const reviewsApi = {
  list: (productId) => api.get(`/products/${productId}/reviews/?product=${productId}`),
  create: (productId, data) =>
    api.post(`/products/${productId}/reviews/`, { product: productId, ...data }),
}

export const ordersApi = {
  list: () => api.get('/orders/'),
  detail: (id) => api.get(`/orders/${id}/`),
  create: (data) => api.post('/orders/', data),
}

export const searchApi = {
  search: (q, sort) => {
    const qs = new URLSearchParams()
    if (q) qs.set('q', q)
    if (sort) qs.set('sort', sort)
    return api.get(`/search/?${qs.toString()}`)
  },
  recommendations: (productId) =>
    api.get(`/recommendations/?product_id=${productId}`),
}
