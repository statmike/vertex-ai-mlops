![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2FExplorations%2FJAX&file=readme.md)
<!--- header table --->
<table align="left">     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/Explorations/JAX/readme.md">
      <img src="https://cloud.google.com/ml-engine/images/github-logo-32px.png" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</table><br/><br/><br/><br/>

---
# /Explorations/JAX/readme.md

A quickly developing framework for transforming numerical functions. Wait? What?

We know [NumPy](https://numpy.org/).  The scientic computing package for Python with a bazillion numerical functions.  It is fast and efficient and even taps into linear algebra accelerators like [Intel MKL](https://software.intel.com/en-us/mkl) and [OpenBLAS](https://www.openblas.net/). NumPy is a fundamental part of TensorFlow and PyTorch as well as many other frameworks for ML.

It turns out all software is just layers of other software - pretty nifty!

In the case of TensorFlow you have accelerators like [XLA](https://www.tensorflow.org/xla) that take atomic operations that are executed individually and colocates them (fusing) to prevent the write+read parts by directly streaming the results.  It manages the code execution and scaling on CPUs, GPUs and TPUs.

Machine learning algorithms like [backpropogation](https://en.wikipedia.org/wiki/Backpropagation) are essential for training neural networks. Hint - its a ton of math.  Math like differentiation.  Back in calculus we learned about differentiation and, in particular, a well named thing called the [chain rule](https://en.wikipedia.org/wiki/Chain_rule).  Basically, express a derivative of a complex function as a chain of derivatives of functions that can compose the complex function.  Ugg, say it again but differently: I don't know the change in $z$ relative to $x$ but if I know the change in $z$ relative to $y$ and the change in $y$ relative to $x$ then I can chain them together!  Wait!  That sounds like a bunch of atomic operations that are exectued individually.  In machine learning we need derivatives, derivatives of derivatives, derivatives of derivatives of derivatives and so on. Let call it automatic differentiation, of which there is a popular Python package called [Autograd](https://github.com/hips/autograd) that differentiates NumPy!

Get it together Mike....

Well, if `Autograd` and `XLA` met, hit it off, decided they like each other, became besties, then they would together be called [JAX](https://github.com/google/jax) and when you hear them talk it would sound like `NumPy`.

In the words of the developers 'JAX is Autograd and XLA, brought together for high-performance machine learning research.'.

## Resources:
- [JAX](https://github.com/google/jax)
- [XLA](https://www.tensorflow.org/xla)
- [Autograd](https://github.com/hips/autograd)
- [NumPy](https://numpy.org/)

## A Developing Ecosystem On Top of JAX:
- [Haiku](https://github.com/deepmind/dm-haiku)
    - a library to simplify the construction of neural network architectures
    - Haiku is to JAX what [Sonnet](https://github.com/deepmind/sonnet) is to TensorFlow 2
- [Flax](https://github.com/google/flax)
    - a libarary for flexible user experience with building neural networks with JAX
- [Equinox](https://github.com/patrick-kidger/equinox)
    - a library for JAX that represents neural networks as PyTrees
    




