import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

// Simple component for testing
function Button({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return <button onClick={onClick}>{children}</button>;
}

describe('Example Test Suite', () => {
  it('should render component', () => {
    render(<Button onClick={() => {}}>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('should handle click event', async () => {
    let clicked = false;
    const handleClick = () => {
      clicked = true;
    };

    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByText('Click me');
    await userEvent.click(button);

    expect(clicked).toBe(true);
  });

  it('should perform basic assertions', () => {
    expect(1 + 1).toBe(2);
    expect('hello').toBeTruthy();
    expect([1, 2, 3]).toHaveLength(3);
  });
});
