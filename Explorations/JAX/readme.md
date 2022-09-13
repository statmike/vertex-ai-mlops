# JAX

A quickly developing framework for transforming numerical functions. Wait? What?

We know [NumPy](https://numpy.org/).  The scientic computing packaged for Python was a bazillion numerical functions.  It is fast and efficient and even taps into linear algebra accelerators like [Intel MKL](https://software.intel.com/en-us/mkl) and [OpenBLAS](https://www.openblas.net/). NumPy is a fundamental part of TensorFlow and PyTorch as well as many other frameworks for ML.

It turns out all software is just layers of other software - pretty nifty!

In the case of TensorFlow you have accelerators like [XLA](https://www.tensorflow.org/xla) that take atomic operations that are executed individually and colocated them (fusing) to prevents the write+read parts by directly streaming the results.  It manages the code execution and scaling on CPUs, GPUs and TPUs.

Machine learning algorithms like [backpropogation](https://en.wikipedia.org/wiki/Backpropagation) are essential from training neural networks. Hint - its a ton of math.  Math like differentiation.  Back in calculus we learned about differentiation and, in particular, a well named thing called the [chain rule](https://en.wikipedia.org/wiki/Chain_rule).  Basically, express a derivitive of a complex function as a chain of derivitives of functions that can compose the complex function.  Ugg, say it again but differently, I don't know the change in $z$ relative to $x$ but if I know the change in $z$ relative to $y$ and the change in $y$ relative to $x$ then I can chain them together!  Wait!  That sounds like a bunch of atomic operations that are exectued individually.  In machine learning we need derivitives, derivitives of derivitives, derivitives of derivitives of derivitives and so on. Let call it automatic differentiation, of which there is a popular Python package called [Autograd](https://github.com/hips/autograd) that differentiates NumPy!

Get it together Mike....

Well, if `Autograd` and `XLA` met, hit it off, decided they like each other, became besties, then they would together be called [JAX](https://github.com/google/jax) and when you hear them talk it would sound like `NumPy`.

In the words of the developers 'JAX is Autograd and XLA, brought together for high-performance machine learning research.'.

Resources:
- [JAX](https://github.com/google/jax)
- [XLA](https://www.tensorflow.org/xla)
- [Autograd](https://github.com/hips/autograd)
- [NumPy](https://numpy.org/)




