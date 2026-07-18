import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import ProductCard from '../components/ProductCard'

const mockProduct = {
  id: 1,
  slug: 'test-product',
  name: 'Test Product',
  category_name: 'Electronics',
  base_price: 29.99,
  average_rating: 4.5,
  review_count: 12,
  is_featured: true,
}

describe('ProductCard', () => {
  it('renders product name', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    expect(screen.getByText('Test Product')).toBeInTheDocument()
  })

  it('renders formatted price', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    expect(screen.getByText('$29.99')).toBeInTheDocument()
  })

  it('renders category name', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    expect(screen.getByText('Electronics')).toBeInTheDocument()
  })

  it('renders rating when rating > 0', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    expect(screen.getByText(/4\.5/)).toBeInTheDocument()
  })

  it('renders featured badge', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    expect(screen.getByText('Featured')).toBeInTheDocument()
  })

  it('links to product detail page', () => {
    render(
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    )
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/product/test-product')
  })
})
