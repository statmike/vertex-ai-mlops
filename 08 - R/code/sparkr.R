n <- 1000000  # Number of random points
x <- runif(n, -1, 1)
y <- runif(n, -1, 1)

inside <- x^2 + y^2 <= 1  # Points within the unit circle
pi_estimate <- 4 * sum(inside) / n 
print(pi_estimate)
