��
��
D
AddV2
x"T
y"T
z"T"
Ttype:
2	��
^
AssignVariableOp
resource
value"dtype"
dtypetype"
validate_shapebool( �
8
Const
output"dtype"
valuetensor"
dtypetype
$
DisableCopyOnRead
resource�
.
Identity

input"T
output"T"	
Ttype
�
MatMul
a"T
b"T
product"T"
transpose_abool( "
transpose_bbool( "
Ttype:
2	"
grad_abool( "
grad_bbool( 
>
Maximum
x"T
y"T
z"T"
Ttype:
2	
�
MergeV2Checkpoints
checkpoint_prefixes
destination_prefix"
delete_old_dirsbool("
allow_missing_filesbool( �

NoOp
M
Pack
values"T*N
output"T"
Nint(0"	
Ttype"
axisint 
C
Placeholder
output"dtype"
dtypetype"
shapeshape:
@
ReadVariableOp
resource
value"dtype"
dtypetype�
@
RealDiv
x"T
y"T
z"T"
Ttype:
2	
E
Relu
features"T
activations"T"
Ttype:
2	
o
	RestoreV2

prefix
tensor_names
shape_and_slices
tensors2dtypes"
dtypes
list(type)(0�
l
SaveV2

prefix
tensor_names
shape_and_slices
tensors2dtypes"
dtypes
list(type)(0�
?
Select
	condition

t"T
e"T
output"T"	
Ttype
H
ShardedFilename
basename	
shard

num_shards
filename
-
Sqrt
x"T
y"T"
Ttype:

2
�
StatefulPartitionedCall
args2Tin
output2Tout"
Tin
list(type)("
Tout
list(type)("	
ffunc"
configstring "
config_protostring "
executor_typestring ��
@
StaticRegexFullMatch	
input

output
"
patternstring
L

StringJoin
inputs*N

output"

Nint("
	separatorstring 
<
Sub
x"T
y"T
z"T"
Ttype:
2	
�
VarHandleOp
resource"
	containerstring "
shared_namestring "

debug_namestring "
dtypetype"
shapeshape"#
allowed_deviceslist(string)
 �
9
VarIsInitializedOp
resource
is_initialized
�"serve*2.18.02v2.18.0-rc2-4-g6550e4bd8028И
�
ConstConst*
_output_shapes

:*
dtype0*�
value�B�"x@{O�n@�N,@�|@$j�?J�?�W�?F��?��?�֗??Z�?P��?�Pe?��}?��M?�PV?%6?�Q?��-?\�(?�`?'�?b?�)�>LI�><
�>Dqn>��$>���=�)|G
�
Const_1Const*
_output_shapes

:*
dtype0*�
value�B�"x�X�G��<!�	�:<���>��;��Z;��<J�6��[�;�\<��軧l$<�)9:�U<\��)� <N/9<. �;1"��[�f���$�:p�t8G�":=���ڹI6��q#7OݰB
�
latent/biasVarHandleOp*
_output_shapes
: *

debug_namelatent/bias/*
dtype0*
shape:*
shared_namelatent/bias
g
latent/bias/Read/ReadVariableOpReadVariableOplatent/bias*
_output_shapes
:*
dtype0
�
latent/kernelVarHandleOp*
_output_shapes
: *

debug_namelatent/kernel/*
dtype0*
shape
:*
shared_namelatent/kernel
o
!latent/kernel/Read/ReadVariableOpReadVariableOplatent/kernel*
_output_shapes

:*
dtype0
�
enc_dense2/biasVarHandleOp*
_output_shapes
: * 

debug_nameenc_dense2/bias/*
dtype0*
shape:* 
shared_nameenc_dense2/bias
o
#enc_dense2/bias/Read/ReadVariableOpReadVariableOpenc_dense2/bias*
_output_shapes
:*
dtype0
�
enc_dense1/biasVarHandleOp*
_output_shapes
: * 

debug_nameenc_dense1/bias/*
dtype0*
shape:* 
shared_nameenc_dense1/bias
o
#enc_dense1/bias/Read/ReadVariableOpReadVariableOpenc_dense1/bias*
_output_shapes
:*
dtype0
�
enc_dense2/kernelVarHandleOp*
_output_shapes
: *"

debug_nameenc_dense2/kernel/*
dtype0*
shape
:*"
shared_nameenc_dense2/kernel
w
%enc_dense2/kernel/Read/ReadVariableOpReadVariableOpenc_dense2/kernel*
_output_shapes

:*
dtype0
�
enc_dense1/kernelVarHandleOp*
_output_shapes
: *"

debug_nameenc_dense1/kernel/*
dtype0*
shape
:*"
shared_nameenc_dense1/kernel
w
%enc_dense1/kernel/Read/ReadVariableOpReadVariableOpenc_dense1/kernel*
_output_shapes

:*
dtype0
�
latent/bias_1VarHandleOp*
_output_shapes
: *

debug_namelatent/bias_1/*
dtype0*
shape:*
shared_namelatent/bias_1
k
!latent/bias_1/Read/ReadVariableOpReadVariableOplatent/bias_1*
_output_shapes
:*
dtype0
�
#Variable/Initializer/ReadVariableOpReadVariableOplatent/bias_1*
_class
loc:@Variable*
_output_shapes
:*
dtype0
�
VariableVarHandleOp*
_class
loc:@Variable*
_output_shapes
: *

debug_name	Variable/*
dtype0*
shape:*
shared_name
Variable
a
)Variable/IsInitialized/VarIsInitializedOpVarIsInitializedOpVariable*
_output_shapes
: 
_
Variable/AssignAssignVariableOpVariable#Variable/Initializer/ReadVariableOp*
dtype0
a
Variable/Read/ReadVariableOpReadVariableOpVariable*
_output_shapes
:*
dtype0
�
latent/kernel_1VarHandleOp*
_output_shapes
: * 

debug_namelatent/kernel_1/*
dtype0*
shape
:* 
shared_namelatent/kernel_1
s
#latent/kernel_1/Read/ReadVariableOpReadVariableOplatent/kernel_1*
_output_shapes

:*
dtype0
�
%Variable_1/Initializer/ReadVariableOpReadVariableOplatent/kernel_1*
_class
loc:@Variable_1*
_output_shapes

:*
dtype0
�

Variable_1VarHandleOp*
_class
loc:@Variable_1*
_output_shapes
: *

debug_nameVariable_1/*
dtype0*
shape
:*
shared_name
Variable_1
e
+Variable_1/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_1*
_output_shapes
: 
e
Variable_1/AssignAssignVariableOp
Variable_1%Variable_1/Initializer/ReadVariableOp*
dtype0
i
Variable_1/Read/ReadVariableOpReadVariableOp
Variable_1*
_output_shapes

:*
dtype0
�
%seed_generator_1/seed_generator_stateVarHandleOp*
_output_shapes
: *6

debug_name(&seed_generator_1/seed_generator_state/*
dtype0	*
shape:*6
shared_name'%seed_generator_1/seed_generator_state
�
9seed_generator_1/seed_generator_state/Read/ReadVariableOpReadVariableOp%seed_generator_1/seed_generator_state*
_output_shapes
:*
dtype0	
�
%Variable_2/Initializer/ReadVariableOpReadVariableOp%seed_generator_1/seed_generator_state*
_class
loc:@Variable_2*
_output_shapes
:*
dtype0	
�

Variable_2VarHandleOp*
_class
loc:@Variable_2*
_output_shapes
: *

debug_nameVariable_2/*
dtype0	*
shape:*
shared_name
Variable_2
e
+Variable_2/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_2*
_output_shapes
: 
e
Variable_2/AssignAssignVariableOp
Variable_2%Variable_2/Initializer/ReadVariableOp*
dtype0	
e
Variable_2/Read/ReadVariableOpReadVariableOp
Variable_2*
_output_shapes
:*
dtype0	
�
enc_dense2/bias_1VarHandleOp*
_output_shapes
: *"

debug_nameenc_dense2/bias_1/*
dtype0*
shape:*"
shared_nameenc_dense2/bias_1
s
%enc_dense2/bias_1/Read/ReadVariableOpReadVariableOpenc_dense2/bias_1*
_output_shapes
:*
dtype0
�
%Variable_3/Initializer/ReadVariableOpReadVariableOpenc_dense2/bias_1*
_class
loc:@Variable_3*
_output_shapes
:*
dtype0
�

Variable_3VarHandleOp*
_class
loc:@Variable_3*
_output_shapes
: *

debug_nameVariable_3/*
dtype0*
shape:*
shared_name
Variable_3
e
+Variable_3/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_3*
_output_shapes
: 
e
Variable_3/AssignAssignVariableOp
Variable_3%Variable_3/Initializer/ReadVariableOp*
dtype0
e
Variable_3/Read/ReadVariableOpReadVariableOp
Variable_3*
_output_shapes
:*
dtype0
�
enc_dense2/kernel_1VarHandleOp*
_output_shapes
: *$

debug_nameenc_dense2/kernel_1/*
dtype0*
shape
:*$
shared_nameenc_dense2/kernel_1
{
'enc_dense2/kernel_1/Read/ReadVariableOpReadVariableOpenc_dense2/kernel_1*
_output_shapes

:*
dtype0
�
%Variable_4/Initializer/ReadVariableOpReadVariableOpenc_dense2/kernel_1*
_class
loc:@Variable_4*
_output_shapes

:*
dtype0
�

Variable_4VarHandleOp*
_class
loc:@Variable_4*
_output_shapes
: *

debug_nameVariable_4/*
dtype0*
shape
:*
shared_name
Variable_4
e
+Variable_4/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_4*
_output_shapes
: 
e
Variable_4/AssignAssignVariableOp
Variable_4%Variable_4/Initializer/ReadVariableOp*
dtype0
i
Variable_4/Read/ReadVariableOpReadVariableOp
Variable_4*
_output_shapes

:*
dtype0
�
#seed_generator/seed_generator_stateVarHandleOp*
_output_shapes
: *4

debug_name&$seed_generator/seed_generator_state/*
dtype0	*
shape:*4
shared_name%#seed_generator/seed_generator_state
�
7seed_generator/seed_generator_state/Read/ReadVariableOpReadVariableOp#seed_generator/seed_generator_state*
_output_shapes
:*
dtype0	
�
%Variable_5/Initializer/ReadVariableOpReadVariableOp#seed_generator/seed_generator_state*
_class
loc:@Variable_5*
_output_shapes
:*
dtype0	
�

Variable_5VarHandleOp*
_class
loc:@Variable_5*
_output_shapes
: *

debug_nameVariable_5/*
dtype0	*
shape:*
shared_name
Variable_5
e
+Variable_5/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_5*
_output_shapes
: 
e
Variable_5/AssignAssignVariableOp
Variable_5%Variable_5/Initializer/ReadVariableOp*
dtype0	
e
Variable_5/Read/ReadVariableOpReadVariableOp
Variable_5*
_output_shapes
:*
dtype0	
�
enc_dense1/bias_1VarHandleOp*
_output_shapes
: *"

debug_nameenc_dense1/bias_1/*
dtype0*
shape:*"
shared_nameenc_dense1/bias_1
s
%enc_dense1/bias_1/Read/ReadVariableOpReadVariableOpenc_dense1/bias_1*
_output_shapes
:*
dtype0
�
%Variable_6/Initializer/ReadVariableOpReadVariableOpenc_dense1/bias_1*
_class
loc:@Variable_6*
_output_shapes
:*
dtype0
�

Variable_6VarHandleOp*
_class
loc:@Variable_6*
_output_shapes
: *

debug_nameVariable_6/*
dtype0*
shape:*
shared_name
Variable_6
e
+Variable_6/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_6*
_output_shapes
: 
e
Variable_6/AssignAssignVariableOp
Variable_6%Variable_6/Initializer/ReadVariableOp*
dtype0
e
Variable_6/Read/ReadVariableOpReadVariableOp
Variable_6*
_output_shapes
:*
dtype0
�
enc_dense1/kernel_1VarHandleOp*
_output_shapes
: *$

debug_nameenc_dense1/kernel_1/*
dtype0*
shape
:*$
shared_nameenc_dense1/kernel_1
{
'enc_dense1/kernel_1/Read/ReadVariableOpReadVariableOpenc_dense1/kernel_1*
_output_shapes

:*
dtype0
�
%Variable_7/Initializer/ReadVariableOpReadVariableOpenc_dense1/kernel_1*
_class
loc:@Variable_7*
_output_shapes

:*
dtype0
�

Variable_7VarHandleOp*
_class
loc:@Variable_7*
_output_shapes
: *

debug_nameVariable_7/*
dtype0*
shape
:*
shared_name
Variable_7
e
+Variable_7/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_7*
_output_shapes
: 
e
Variable_7/AssignAssignVariableOp
Variable_7%Variable_7/Initializer/ReadVariableOp*
dtype0
i
Variable_7/Read/ReadVariableOpReadVariableOp
Variable_7*
_output_shapes

:*
dtype0
�
normalization/countVarHandleOp*
_output_shapes
: *$

debug_namenormalization/count/*
dtype0	*
shape: *$
shared_namenormalization/count
s
'normalization/count/Read/ReadVariableOpReadVariableOpnormalization/count*
_output_shapes
: *
dtype0	
�
%Variable_8/Initializer/ReadVariableOpReadVariableOpnormalization/count*
_class
loc:@Variable_8*
_output_shapes
: *
dtype0	
�

Variable_8VarHandleOp*
_class
loc:@Variable_8*
_output_shapes
: *

debug_nameVariable_8/*
dtype0	*
shape: *
shared_name
Variable_8
e
+Variable_8/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_8*
_output_shapes
: 
e
Variable_8/AssignAssignVariableOp
Variable_8%Variable_8/Initializer/ReadVariableOp*
dtype0	
a
Variable_8/Read/ReadVariableOpReadVariableOp
Variable_8*
_output_shapes
: *
dtype0	
�
normalization/varianceVarHandleOp*
_output_shapes
: *'

debug_namenormalization/variance/*
dtype0*
shape:*'
shared_namenormalization/variance
}
*normalization/variance/Read/ReadVariableOpReadVariableOpnormalization/variance*
_output_shapes
:*
dtype0
�
%Variable_9/Initializer/ReadVariableOpReadVariableOpnormalization/variance*
_class
loc:@Variable_9*
_output_shapes
:*
dtype0
�

Variable_9VarHandleOp*
_class
loc:@Variable_9*
_output_shapes
: *

debug_nameVariable_9/*
dtype0*
shape:*
shared_name
Variable_9
e
+Variable_9/IsInitialized/VarIsInitializedOpVarIsInitializedOp
Variable_9*
_output_shapes
: 
e
Variable_9/AssignAssignVariableOp
Variable_9%Variable_9/Initializer/ReadVariableOp*
dtype0
e
Variable_9/Read/ReadVariableOpReadVariableOp
Variable_9*
_output_shapes
:*
dtype0
�
normalization/meanVarHandleOp*
_output_shapes
: *#

debug_namenormalization/mean/*
dtype0*
shape:*#
shared_namenormalization/mean
u
&normalization/mean/Read/ReadVariableOpReadVariableOpnormalization/mean*
_output_shapes
:*
dtype0
�
&Variable_10/Initializer/ReadVariableOpReadVariableOpnormalization/mean*
_class
loc:@Variable_10*
_output_shapes
:*
dtype0
�
Variable_10VarHandleOp*
_class
loc:@Variable_10*
_output_shapes
: *

debug_nameVariable_10/*
dtype0*
shape:*
shared_nameVariable_10
g
,Variable_10/IsInitialized/VarIsInitializedOpVarIsInitializedOpVariable_10*
_output_shapes
: 
h
Variable_10/AssignAssignVariableOpVariable_10&Variable_10/Initializer/ReadVariableOp*
dtype0
g
Variable_10/Read/ReadVariableOpReadVariableOpVariable_10*
_output_shapes
:*
dtype0
t
serve_input_layerPlaceholder*'
_output_shapes
:���������*
dtype0*
shape:���������
�
StatefulPartitionedCallStatefulPartitionedCallserve_input_layerConst_1Constenc_dense1/kernel_1enc_dense1/bias_1enc_dense2/kernel_1enc_dense2/bias_1latent/kernel_1latent/bias_1*
Tin
2	*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*(
_read_only_resource_inputs

*2
config_proto" 

CPU

GPU 2J 8� �J *6
f1R/
-__inference_signature_wrapper___call___569896
~
serving_default_input_layerPlaceholder*'
_output_shapes
:���������*
dtype0*
shape:���������
�
StatefulPartitionedCall_1StatefulPartitionedCallserving_default_input_layerConst_1Constenc_dense1/kernel_1enc_dense1/bias_1enc_dense2/kernel_1enc_dense2/bias_1latent/kernel_1latent/bias_1*
Tin
2	*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*(
_read_only_resource_inputs

*2
config_proto" 

CPU

GPU 2J 8� �J *6
f1R/
-__inference_signature_wrapper___call___569917

NoOpNoOp
�
Const_2Const"/device:CPU:0*
_output_shapes
: *
dtype0*�
value�B� B�
�
	variables
trainable_variables
non_trainable_variables
_all_variables
_misc_assets
	serve

signatures*
R
0
	1

2
3
4
5
6
7
8
9
10*
.
0
1
2
3
4
5*
'
0
	1

2
3
4*
.
0
1
2
3
4
5*
* 

trace_0* 
"
	serve
serving_default* 
KE
VARIABLE_VALUEVariable_10&variables/0/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_9&variables/1/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_8&variables/2/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_7&variables/3/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_6&variables/4/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_5&variables/5/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_4&variables/6/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_3&variables/7/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_2&variables/8/.ATTRIBUTES/VARIABLE_VALUE*
JD
VARIABLE_VALUE
Variable_1&variables/9/.ATTRIBUTES/VARIABLE_VALUE*
IC
VARIABLE_VALUEVariable'variables/10/.ATTRIBUTES/VARIABLE_VALUE*
XR
VARIABLE_VALUEenc_dense1/kernel_1+_all_variables/0/.ATTRIBUTES/VARIABLE_VALUE*
XR
VARIABLE_VALUEenc_dense2/kernel_1+_all_variables/1/.ATTRIBUTES/VARIABLE_VALUE*
VP
VARIABLE_VALUEenc_dense1/bias_1+_all_variables/2/.ATTRIBUTES/VARIABLE_VALUE*
VP
VARIABLE_VALUEenc_dense2/bias_1+_all_variables/3/.ATTRIBUTES/VARIABLE_VALUE*
TN
VARIABLE_VALUElatent/kernel_1+_all_variables/4/.ATTRIBUTES/VARIABLE_VALUE*
RL
VARIABLE_VALUElatent/bias_1+_all_variables/5/.ATTRIBUTES/VARIABLE_VALUE*
 
	capture_0
	capture_1* 
 
	capture_0
	capture_1* 
 
	capture_0
	capture_1* 
* 
* 
O
saver_filenamePlaceholder*
_output_shapes
: *
dtype0*
shape: 
�
StatefulPartitionedCall_2StatefulPartitionedCallsaver_filenameVariable_10
Variable_9
Variable_8
Variable_7
Variable_6
Variable_5
Variable_4
Variable_3
Variable_2
Variable_1Variableenc_dense1/kernel_1enc_dense2/kernel_1enc_dense1/bias_1enc_dense2/bias_1latent/kernel_1latent/bias_1Const_2*
Tin
2*
Tout
2*
_collective_manager_ids
 *
_output_shapes
: * 
_read_only_resource_inputs
 *2
config_proto" 

CPU

GPU 2J 8� �J *(
f#R!
__inference__traced_save_570089
�
StatefulPartitionedCall_3StatefulPartitionedCallsaver_filenameVariable_10
Variable_9
Variable_8
Variable_7
Variable_6
Variable_5
Variable_4
Variable_3
Variable_2
Variable_1Variableenc_dense1/kernel_1enc_dense2/kernel_1enc_dense1/bias_1enc_dense2/bias_1latent/kernel_1latent/bias_1*
Tin
2*
Tout
2*
_collective_manager_ids
 *
_output_shapes
: * 
_read_only_resource_inputs
 *2
config_proto" 

CPU

GPU 2J 8� �J *+
f&R$
"__inference__traced_restore_570149��
�N
�	
"__inference__traced_restore_570149
file_prefix*
assignvariableop_variable_10:+
assignvariableop_1_variable_9:'
assignvariableop_2_variable_8:	 /
assignvariableop_3_variable_7:+
assignvariableop_4_variable_6:+
assignvariableop_5_variable_5:	/
assignvariableop_6_variable_4:+
assignvariableop_7_variable_3:+
assignvariableop_8_variable_2:	/
assignvariableop_9_variable_1:*
assignvariableop_10_variable:9
'assignvariableop_11_enc_dense1_kernel_1:9
'assignvariableop_12_enc_dense2_kernel_1:3
%assignvariableop_13_enc_dense1_bias_1:3
%assignvariableop_14_enc_dense2_bias_1:5
#assignvariableop_15_latent_kernel_1:/
!assignvariableop_16_latent_bias_1:
identity_18��AssignVariableOp�AssignVariableOp_1�AssignVariableOp_10�AssignVariableOp_11�AssignVariableOp_12�AssignVariableOp_13�AssignVariableOp_14�AssignVariableOp_15�AssignVariableOp_16�AssignVariableOp_2�AssignVariableOp_3�AssignVariableOp_4�AssignVariableOp_5�AssignVariableOp_6�AssignVariableOp_7�AssignVariableOp_8�AssignVariableOp_9�
RestoreV2/tensor_namesConst"/device:CPU:0*
_output_shapes
:*
dtype0*�
value�B�B&variables/0/.ATTRIBUTES/VARIABLE_VALUEB&variables/1/.ATTRIBUTES/VARIABLE_VALUEB&variables/2/.ATTRIBUTES/VARIABLE_VALUEB&variables/3/.ATTRIBUTES/VARIABLE_VALUEB&variables/4/.ATTRIBUTES/VARIABLE_VALUEB&variables/5/.ATTRIBUTES/VARIABLE_VALUEB&variables/6/.ATTRIBUTES/VARIABLE_VALUEB&variables/7/.ATTRIBUTES/VARIABLE_VALUEB&variables/8/.ATTRIBUTES/VARIABLE_VALUEB&variables/9/.ATTRIBUTES/VARIABLE_VALUEB'variables/10/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/0/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/1/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/2/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/3/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/4/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/5/.ATTRIBUTES/VARIABLE_VALUEB_CHECKPOINTABLE_OBJECT_GRAPH�
RestoreV2/shape_and_slicesConst"/device:CPU:0*
_output_shapes
:*
dtype0*7
value.B,B B B B B B B B B B B B B B B B B B �
	RestoreV2	RestoreV2file_prefixRestoreV2/tensor_names:output:0#RestoreV2/shape_and_slices:output:0"/device:CPU:0*\
_output_shapesJ
H::::::::::::::::::* 
dtypes
2			[
IdentityIdentityRestoreV2:tensors:0"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOpAssignVariableOpassignvariableop_variable_10Identity:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_1IdentityRestoreV2:tensors:1"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_1AssignVariableOpassignvariableop_1_variable_9Identity_1:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_2IdentityRestoreV2:tensors:2"/device:CPU:0*
T0	*
_output_shapes
:�
AssignVariableOp_2AssignVariableOpassignvariableop_2_variable_8Identity_2:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0	]

Identity_3IdentityRestoreV2:tensors:3"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_3AssignVariableOpassignvariableop_3_variable_7Identity_3:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_4IdentityRestoreV2:tensors:4"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_4AssignVariableOpassignvariableop_4_variable_6Identity_4:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_5IdentityRestoreV2:tensors:5"/device:CPU:0*
T0	*
_output_shapes
:�
AssignVariableOp_5AssignVariableOpassignvariableop_5_variable_5Identity_5:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0	]

Identity_6IdentityRestoreV2:tensors:6"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_6AssignVariableOpassignvariableop_6_variable_4Identity_6:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_7IdentityRestoreV2:tensors:7"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_7AssignVariableOpassignvariableop_7_variable_3Identity_7:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0]

Identity_8IdentityRestoreV2:tensors:8"/device:CPU:0*
T0	*
_output_shapes
:�
AssignVariableOp_8AssignVariableOpassignvariableop_8_variable_2Identity_8:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0	]

Identity_9IdentityRestoreV2:tensors:9"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_9AssignVariableOpassignvariableop_9_variable_1Identity_9:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_10IdentityRestoreV2:tensors:10"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_10AssignVariableOpassignvariableop_10_variableIdentity_10:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_11IdentityRestoreV2:tensors:11"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_11AssignVariableOp'assignvariableop_11_enc_dense1_kernel_1Identity_11:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_12IdentityRestoreV2:tensors:12"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_12AssignVariableOp'assignvariableop_12_enc_dense2_kernel_1Identity_12:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_13IdentityRestoreV2:tensors:13"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_13AssignVariableOp%assignvariableop_13_enc_dense1_bias_1Identity_13:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_14IdentityRestoreV2:tensors:14"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_14AssignVariableOp%assignvariableop_14_enc_dense2_bias_1Identity_14:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_15IdentityRestoreV2:tensors:15"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_15AssignVariableOp#assignvariableop_15_latent_kernel_1Identity_15:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0_
Identity_16IdentityRestoreV2:tensors:16"/device:CPU:0*
T0*
_output_shapes
:�
AssignVariableOp_16AssignVariableOp!assignvariableop_16_latent_bias_1Identity_16:output:0"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 *
dtype0Y
NoOpNoOp"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 �
Identity_17Identityfile_prefix^AssignVariableOp^AssignVariableOp_1^AssignVariableOp_10^AssignVariableOp_11^AssignVariableOp_12^AssignVariableOp_13^AssignVariableOp_14^AssignVariableOp_15^AssignVariableOp_16^AssignVariableOp_2^AssignVariableOp_3^AssignVariableOp_4^AssignVariableOp_5^AssignVariableOp_6^AssignVariableOp_7^AssignVariableOp_8^AssignVariableOp_9^NoOp"/device:CPU:0*
T0*
_output_shapes
: W
Identity_18IdentityIdentity_17:output:0^NoOp_1*
T0*
_output_shapes
: �
NoOp_1NoOp^AssignVariableOp^AssignVariableOp_1^AssignVariableOp_10^AssignVariableOp_11^AssignVariableOp_12^AssignVariableOp_13^AssignVariableOp_14^AssignVariableOp_15^AssignVariableOp_16^AssignVariableOp_2^AssignVariableOp_3^AssignVariableOp_4^AssignVariableOp_5^AssignVariableOp_6^AssignVariableOp_7^AssignVariableOp_8^AssignVariableOp_9*
_output_shapes
 "#
identity_18Identity_18:output:0*(
_construction_contextkEagerRuntime*7
_input_shapes&
$: : : : : : : : : : : : : : : : : : 2*
AssignVariableOp_10AssignVariableOp_102*
AssignVariableOp_11AssignVariableOp_112*
AssignVariableOp_12AssignVariableOp_122*
AssignVariableOp_13AssignVariableOp_132*
AssignVariableOp_14AssignVariableOp_142*
AssignVariableOp_15AssignVariableOp_152*
AssignVariableOp_16AssignVariableOp_162(
AssignVariableOp_1AssignVariableOp_12(
AssignVariableOp_2AssignVariableOp_22(
AssignVariableOp_3AssignVariableOp_32(
AssignVariableOp_4AssignVariableOp_42(
AssignVariableOp_5AssignVariableOp_52(
AssignVariableOp_6AssignVariableOp_62(
AssignVariableOp_7AssignVariableOp_72(
AssignVariableOp_8AssignVariableOp_82(
AssignVariableOp_9AssignVariableOp_92$
AssignVariableOpAssignVariableOp:-)
'
_user_specified_namelatent/bias_1:/+
)
_user_specified_namelatent/kernel_1:1-
+
_user_specified_nameenc_dense2/bias_1:1-
+
_user_specified_nameenc_dense1/bias_1:3/
-
_user_specified_nameenc_dense2/kernel_1:3/
-
_user_specified_nameenc_dense1/kernel_1:($
"
_user_specified_name
Variable:*
&
$
_user_specified_name
Variable_1:*	&
$
_user_specified_name
Variable_2:*&
$
_user_specified_name
Variable_3:*&
$
_user_specified_name
Variable_4:*&
$
_user_specified_name
Variable_5:*&
$
_user_specified_name
Variable_6:*&
$
_user_specified_name
Variable_7:*&
$
_user_specified_name
Variable_8:*&
$
_user_specified_name
Variable_9:+'
%
_user_specified_nameVariable_10:C ?

_output_shapes
: 
%
_user_specified_namefile_prefix
�0
�
__inference___call___569874
input_layer%
!embedding_1_normalization_1_sub_y&
"embedding_1_normalization_1_sqrt_xQ
?embedding_1_encoder_1_enc_dense1_1_cast_readvariableop_resource:L
>embedding_1_encoder_1_enc_dense1_1_add_readvariableop_resource:Q
?embedding_1_encoder_1_enc_dense2_1_cast_readvariableop_resource:L
>embedding_1_encoder_1_enc_dense2_1_add_readvariableop_resource:M
;embedding_1_encoder_1_latent_1_cast_readvariableop_resource:H
:embedding_1_encoder_1_latent_1_add_readvariableop_resource:
identity��5embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOp�6embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOp�5embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOp�6embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOp�1embedding_1/encoder_1/latent_1/Add/ReadVariableOp�2embedding_1/encoder_1/latent_1/Cast/ReadVariableOp�
embedding_1/normalization_1/SubSubinput_layer!embedding_1_normalization_1_sub_y*
T0*'
_output_shapes
:���������u
 embedding_1/normalization_1/SqrtSqrt"embedding_1_normalization_1_sqrt_x*
T0*
_output_shapes

:f
!embedding_1/normalization_1/ConstConst*
_output_shapes
: *
dtype0*
valueB
 *���3�
#embedding_1/normalization_1/MaximumMaximum$embedding_1/normalization_1/Sqrt:y:0*embedding_1/normalization_1/Const:output:0*
T0*
_output_shapes

:�
#embedding_1/normalization_1/truedivRealDiv#embedding_1/normalization_1/Sub:z:0'embedding_1/normalization_1/Maximum:z:0*
T0*'
_output_shapes
:����������
6embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOpReadVariableOp?embedding_1_encoder_1_enc_dense1_1_cast_readvariableop_resource*
_output_shapes

:*
dtype0�
)embedding_1/encoder_1/enc_dense1_1/MatMulMatMul'embedding_1/normalization_1/truediv:z:0>embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
5embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOpReadVariableOp>embedding_1_encoder_1_enc_dense1_1_add_readvariableop_resource*
_output_shapes
:*
dtype0�
&embedding_1/encoder_1/enc_dense1_1/AddAddV23embedding_1/encoder_1/enc_dense1_1/MatMul:product:0=embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
'embedding_1/encoder_1/enc_dense1_1/ReluRelu*embedding_1/encoder_1/enc_dense1_1/Add:z:0*
T0*'
_output_shapes
:����������
6embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOpReadVariableOp?embedding_1_encoder_1_enc_dense2_1_cast_readvariableop_resource*
_output_shapes

:*
dtype0�
)embedding_1/encoder_1/enc_dense2_1/MatMulMatMul5embedding_1/encoder_1/enc_dense1_1/Relu:activations:0>embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
5embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOpReadVariableOp>embedding_1_encoder_1_enc_dense2_1_add_readvariableop_resource*
_output_shapes
:*
dtype0�
&embedding_1/encoder_1/enc_dense2_1/AddAddV23embedding_1/encoder_1/enc_dense2_1/MatMul:product:0=embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
'embedding_1/encoder_1/enc_dense2_1/ReluRelu*embedding_1/encoder_1/enc_dense2_1/Add:z:0*
T0*'
_output_shapes
:����������
2embedding_1/encoder_1/latent_1/Cast/ReadVariableOpReadVariableOp;embedding_1_encoder_1_latent_1_cast_readvariableop_resource*
_output_shapes

:*
dtype0�
%embedding_1/encoder_1/latent_1/MatMulMatMul5embedding_1/encoder_1/enc_dense2_1/Relu:activations:0:embedding_1/encoder_1/latent_1/Cast/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
1embedding_1/encoder_1/latent_1/Add/ReadVariableOpReadVariableOp:embedding_1_encoder_1_latent_1_add_readvariableop_resource*
_output_shapes
:*
dtype0�
"embedding_1/encoder_1/latent_1/AddAddV2/embedding_1/encoder_1/latent_1/MatMul:product:09embedding_1/encoder_1/latent_1/Add/ReadVariableOp:value:0*
T0*'
_output_shapes
:����������
#embedding_1/encoder_1/latent_1/ReluRelu&embedding_1/encoder_1/latent_1/Add:z:0*
T0*'
_output_shapes
:����������
IdentityIdentity1embedding_1/encoder_1/latent_1/Relu:activations:0^NoOp*
T0*'
_output_shapes
:����������
NoOpNoOp6^embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOp7^embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOp6^embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOp7^embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOp2^embedding_1/encoder_1/latent_1/Add/ReadVariableOp3^embedding_1/encoder_1/latent_1/Cast/ReadVariableOp*
_output_shapes
 "
identityIdentity:output:0*(
_construction_contextkEagerRuntime*F
_input_shapes5
3:���������::: : : : : : 2n
5embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOp5embedding_1/encoder_1/enc_dense1_1/Add/ReadVariableOp2p
6embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOp6embedding_1/encoder_1/enc_dense1_1/Cast/ReadVariableOp2n
5embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOp5embedding_1/encoder_1/enc_dense2_1/Add/ReadVariableOp2p
6embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOp6embedding_1/encoder_1/enc_dense2_1/Cast/ReadVariableOp2f
1embedding_1/encoder_1/latent_1/Add/ReadVariableOp1embedding_1/encoder_1/latent_1/Add/ReadVariableOp2h
2embedding_1/encoder_1/latent_1/Cast/ReadVariableOp2embedding_1/encoder_1/latent_1/Cast/ReadVariableOp:($
"
_user_specified_name
resource:($
"
_user_specified_name
resource:($
"
_user_specified_name
resource:($
"
_user_specified_name
resource:($
"
_user_specified_name
resource:($
"
_user_specified_name
resource:$ 

_output_shapes

::$ 

_output_shapes

::T P
'
_output_shapes
:���������
%
_user_specified_nameinput_layer
��
�
__inference__traced_save_570089
file_prefix0
"read_disablecopyonread_variable_10:1
#read_1_disablecopyonread_variable_9:-
#read_2_disablecopyonread_variable_8:	 5
#read_3_disablecopyonread_variable_7:1
#read_4_disablecopyonread_variable_6:1
#read_5_disablecopyonread_variable_5:	5
#read_6_disablecopyonread_variable_4:1
#read_7_disablecopyonread_variable_3:1
#read_8_disablecopyonread_variable_2:	5
#read_9_disablecopyonread_variable_1:0
"read_10_disablecopyonread_variable:?
-read_11_disablecopyonread_enc_dense1_kernel_1:?
-read_12_disablecopyonread_enc_dense2_kernel_1:9
+read_13_disablecopyonread_enc_dense1_bias_1:9
+read_14_disablecopyonread_enc_dense2_bias_1:;
)read_15_disablecopyonread_latent_kernel_1:5
'read_16_disablecopyonread_latent_bias_1:
savev2_const_2
identity_35��MergeV2Checkpoints�Read/DisableCopyOnRead�Read/ReadVariableOp�Read_1/DisableCopyOnRead�Read_1/ReadVariableOp�Read_10/DisableCopyOnRead�Read_10/ReadVariableOp�Read_11/DisableCopyOnRead�Read_11/ReadVariableOp�Read_12/DisableCopyOnRead�Read_12/ReadVariableOp�Read_13/DisableCopyOnRead�Read_13/ReadVariableOp�Read_14/DisableCopyOnRead�Read_14/ReadVariableOp�Read_15/DisableCopyOnRead�Read_15/ReadVariableOp�Read_16/DisableCopyOnRead�Read_16/ReadVariableOp�Read_2/DisableCopyOnRead�Read_2/ReadVariableOp�Read_3/DisableCopyOnRead�Read_3/ReadVariableOp�Read_4/DisableCopyOnRead�Read_4/ReadVariableOp�Read_5/DisableCopyOnRead�Read_5/ReadVariableOp�Read_6/DisableCopyOnRead�Read_6/ReadVariableOp�Read_7/DisableCopyOnRead�Read_7/ReadVariableOp�Read_8/DisableCopyOnRead�Read_8/ReadVariableOp�Read_9/DisableCopyOnRead�Read_9/ReadVariableOpw
StaticRegexFullMatchStaticRegexFullMatchfile_prefix"/device:CPU:**
_output_shapes
: *
pattern
^s3://.*Z
ConstConst"/device:CPU:**
_output_shapes
: *
dtype0*
valueB B.parta
Const_1Const"/device:CPU:**
_output_shapes
: *
dtype0*
valueB B
_temp/part�
SelectSelectStaticRegexFullMatch:output:0Const:output:0Const_1:output:0"/device:CPU:**
T0*
_output_shapes
: f

StringJoin
StringJoinfile_prefixSelect:output:0"/device:CPU:**
N*
_output_shapes
: e
Read/DisableCopyOnReadDisableCopyOnRead"read_disablecopyonread_variable_10*
_output_shapes
 �
Read/ReadVariableOpReadVariableOp"read_disablecopyonread_variable_10^Read/DisableCopyOnRead*
_output_shapes
:*
dtype0V
IdentityIdentityRead/ReadVariableOp:value:0*
T0*
_output_shapes
:]

Identity_1IdentityIdentity:output:0"/device:CPU:0*
T0*
_output_shapes
:h
Read_1/DisableCopyOnReadDisableCopyOnRead#read_1_disablecopyonread_variable_9*
_output_shapes
 �
Read_1/ReadVariableOpReadVariableOp#read_1_disablecopyonread_variable_9^Read_1/DisableCopyOnRead*
_output_shapes
:*
dtype0Z

Identity_2IdentityRead_1/ReadVariableOp:value:0*
T0*
_output_shapes
:_

Identity_3IdentityIdentity_2:output:0"/device:CPU:0*
T0*
_output_shapes
:h
Read_2/DisableCopyOnReadDisableCopyOnRead#read_2_disablecopyonread_variable_8*
_output_shapes
 �
Read_2/ReadVariableOpReadVariableOp#read_2_disablecopyonread_variable_8^Read_2/DisableCopyOnRead*
_output_shapes
: *
dtype0	V

Identity_4IdentityRead_2/ReadVariableOp:value:0*
T0	*
_output_shapes
: [

Identity_5IdentityIdentity_4:output:0"/device:CPU:0*
T0	*
_output_shapes
: h
Read_3/DisableCopyOnReadDisableCopyOnRead#read_3_disablecopyonread_variable_7*
_output_shapes
 �
Read_3/ReadVariableOpReadVariableOp#read_3_disablecopyonread_variable_7^Read_3/DisableCopyOnRead*
_output_shapes

:*
dtype0^

Identity_6IdentityRead_3/ReadVariableOp:value:0*
T0*
_output_shapes

:c

Identity_7IdentityIdentity_6:output:0"/device:CPU:0*
T0*
_output_shapes

:h
Read_4/DisableCopyOnReadDisableCopyOnRead#read_4_disablecopyonread_variable_6*
_output_shapes
 �
Read_4/ReadVariableOpReadVariableOp#read_4_disablecopyonread_variable_6^Read_4/DisableCopyOnRead*
_output_shapes
:*
dtype0Z

Identity_8IdentityRead_4/ReadVariableOp:value:0*
T0*
_output_shapes
:_

Identity_9IdentityIdentity_8:output:0"/device:CPU:0*
T0*
_output_shapes
:h
Read_5/DisableCopyOnReadDisableCopyOnRead#read_5_disablecopyonread_variable_5*
_output_shapes
 �
Read_5/ReadVariableOpReadVariableOp#read_5_disablecopyonread_variable_5^Read_5/DisableCopyOnRead*
_output_shapes
:*
dtype0	[
Identity_10IdentityRead_5/ReadVariableOp:value:0*
T0	*
_output_shapes
:a
Identity_11IdentityIdentity_10:output:0"/device:CPU:0*
T0	*
_output_shapes
:h
Read_6/DisableCopyOnReadDisableCopyOnRead#read_6_disablecopyonread_variable_4*
_output_shapes
 �
Read_6/ReadVariableOpReadVariableOp#read_6_disablecopyonread_variable_4^Read_6/DisableCopyOnRead*
_output_shapes

:*
dtype0_
Identity_12IdentityRead_6/ReadVariableOp:value:0*
T0*
_output_shapes

:e
Identity_13IdentityIdentity_12:output:0"/device:CPU:0*
T0*
_output_shapes

:h
Read_7/DisableCopyOnReadDisableCopyOnRead#read_7_disablecopyonread_variable_3*
_output_shapes
 �
Read_7/ReadVariableOpReadVariableOp#read_7_disablecopyonread_variable_3^Read_7/DisableCopyOnRead*
_output_shapes
:*
dtype0[
Identity_14IdentityRead_7/ReadVariableOp:value:0*
T0*
_output_shapes
:a
Identity_15IdentityIdentity_14:output:0"/device:CPU:0*
T0*
_output_shapes
:h
Read_8/DisableCopyOnReadDisableCopyOnRead#read_8_disablecopyonread_variable_2*
_output_shapes
 �
Read_8/ReadVariableOpReadVariableOp#read_8_disablecopyonread_variable_2^Read_8/DisableCopyOnRead*
_output_shapes
:*
dtype0	[
Identity_16IdentityRead_8/ReadVariableOp:value:0*
T0	*
_output_shapes
:a
Identity_17IdentityIdentity_16:output:0"/device:CPU:0*
T0	*
_output_shapes
:h
Read_9/DisableCopyOnReadDisableCopyOnRead#read_9_disablecopyonread_variable_1*
_output_shapes
 �
Read_9/ReadVariableOpReadVariableOp#read_9_disablecopyonread_variable_1^Read_9/DisableCopyOnRead*
_output_shapes

:*
dtype0_
Identity_18IdentityRead_9/ReadVariableOp:value:0*
T0*
_output_shapes

:e
Identity_19IdentityIdentity_18:output:0"/device:CPU:0*
T0*
_output_shapes

:h
Read_10/DisableCopyOnReadDisableCopyOnRead"read_10_disablecopyonread_variable*
_output_shapes
 �
Read_10/ReadVariableOpReadVariableOp"read_10_disablecopyonread_variable^Read_10/DisableCopyOnRead*
_output_shapes
:*
dtype0\
Identity_20IdentityRead_10/ReadVariableOp:value:0*
T0*
_output_shapes
:a
Identity_21IdentityIdentity_20:output:0"/device:CPU:0*
T0*
_output_shapes
:s
Read_11/DisableCopyOnReadDisableCopyOnRead-read_11_disablecopyonread_enc_dense1_kernel_1*
_output_shapes
 �
Read_11/ReadVariableOpReadVariableOp-read_11_disablecopyonread_enc_dense1_kernel_1^Read_11/DisableCopyOnRead*
_output_shapes

:*
dtype0`
Identity_22IdentityRead_11/ReadVariableOp:value:0*
T0*
_output_shapes

:e
Identity_23IdentityIdentity_22:output:0"/device:CPU:0*
T0*
_output_shapes

:s
Read_12/DisableCopyOnReadDisableCopyOnRead-read_12_disablecopyonread_enc_dense2_kernel_1*
_output_shapes
 �
Read_12/ReadVariableOpReadVariableOp-read_12_disablecopyonread_enc_dense2_kernel_1^Read_12/DisableCopyOnRead*
_output_shapes

:*
dtype0`
Identity_24IdentityRead_12/ReadVariableOp:value:0*
T0*
_output_shapes

:e
Identity_25IdentityIdentity_24:output:0"/device:CPU:0*
T0*
_output_shapes

:q
Read_13/DisableCopyOnReadDisableCopyOnRead+read_13_disablecopyonread_enc_dense1_bias_1*
_output_shapes
 �
Read_13/ReadVariableOpReadVariableOp+read_13_disablecopyonread_enc_dense1_bias_1^Read_13/DisableCopyOnRead*
_output_shapes
:*
dtype0\
Identity_26IdentityRead_13/ReadVariableOp:value:0*
T0*
_output_shapes
:a
Identity_27IdentityIdentity_26:output:0"/device:CPU:0*
T0*
_output_shapes
:q
Read_14/DisableCopyOnReadDisableCopyOnRead+read_14_disablecopyonread_enc_dense2_bias_1*
_output_shapes
 �
Read_14/ReadVariableOpReadVariableOp+read_14_disablecopyonread_enc_dense2_bias_1^Read_14/DisableCopyOnRead*
_output_shapes
:*
dtype0\
Identity_28IdentityRead_14/ReadVariableOp:value:0*
T0*
_output_shapes
:a
Identity_29IdentityIdentity_28:output:0"/device:CPU:0*
T0*
_output_shapes
:o
Read_15/DisableCopyOnReadDisableCopyOnRead)read_15_disablecopyonread_latent_kernel_1*
_output_shapes
 �
Read_15/ReadVariableOpReadVariableOp)read_15_disablecopyonread_latent_kernel_1^Read_15/DisableCopyOnRead*
_output_shapes

:*
dtype0`
Identity_30IdentityRead_15/ReadVariableOp:value:0*
T0*
_output_shapes

:e
Identity_31IdentityIdentity_30:output:0"/device:CPU:0*
T0*
_output_shapes

:m
Read_16/DisableCopyOnReadDisableCopyOnRead'read_16_disablecopyonread_latent_bias_1*
_output_shapes
 �
Read_16/ReadVariableOpReadVariableOp'read_16_disablecopyonread_latent_bias_1^Read_16/DisableCopyOnRead*
_output_shapes
:*
dtype0\
Identity_32IdentityRead_16/ReadVariableOp:value:0*
T0*
_output_shapes
:a
Identity_33IdentityIdentity_32:output:0"/device:CPU:0*
T0*
_output_shapes
:L

num_shardsConst*
_output_shapes
: *
dtype0*
value	B :f
ShardedFilename/shardConst"/device:CPU:0*
_output_shapes
: *
dtype0*
value	B : �
ShardedFilenameShardedFilenameStringJoin:output:0ShardedFilename/shard:output:0num_shards:output:0"/device:CPU:0*
_output_shapes
: �
SaveV2/tensor_namesConst"/device:CPU:0*
_output_shapes
:*
dtype0*�
value�B�B&variables/0/.ATTRIBUTES/VARIABLE_VALUEB&variables/1/.ATTRIBUTES/VARIABLE_VALUEB&variables/2/.ATTRIBUTES/VARIABLE_VALUEB&variables/3/.ATTRIBUTES/VARIABLE_VALUEB&variables/4/.ATTRIBUTES/VARIABLE_VALUEB&variables/5/.ATTRIBUTES/VARIABLE_VALUEB&variables/6/.ATTRIBUTES/VARIABLE_VALUEB&variables/7/.ATTRIBUTES/VARIABLE_VALUEB&variables/8/.ATTRIBUTES/VARIABLE_VALUEB&variables/9/.ATTRIBUTES/VARIABLE_VALUEB'variables/10/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/0/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/1/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/2/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/3/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/4/.ATTRIBUTES/VARIABLE_VALUEB+_all_variables/5/.ATTRIBUTES/VARIABLE_VALUEB_CHECKPOINTABLE_OBJECT_GRAPH�
SaveV2/shape_and_slicesConst"/device:CPU:0*
_output_shapes
:*
dtype0*7
value.B,B B B B B B B B B B B B B B B B B B �
SaveV2SaveV2ShardedFilename:filename:0SaveV2/tensor_names:output:0 SaveV2/shape_and_slices:output:0Identity_1:output:0Identity_3:output:0Identity_5:output:0Identity_7:output:0Identity_9:output:0Identity_11:output:0Identity_13:output:0Identity_15:output:0Identity_17:output:0Identity_19:output:0Identity_21:output:0Identity_23:output:0Identity_25:output:0Identity_27:output:0Identity_29:output:0Identity_31:output:0Identity_33:output:0savev2_const_2"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 * 
dtypes
2			�
&MergeV2Checkpoints/checkpoint_prefixesPackShardedFilename:filename:0^SaveV2"/device:CPU:0*
N*
T0*
_output_shapes
:�
MergeV2CheckpointsMergeV2Checkpoints/MergeV2Checkpoints/checkpoint_prefixes:output:0file_prefix"/device:CPU:0*&
 _has_manual_control_dependencies(*
_output_shapes
 i
Identity_34Identityfile_prefix^MergeV2Checkpoints"/device:CPU:0*
T0*
_output_shapes
: U
Identity_35IdentityIdentity_34:output:0^NoOp*
T0*
_output_shapes
: �
NoOpNoOp^MergeV2Checkpoints^Read/DisableCopyOnRead^Read/ReadVariableOp^Read_1/DisableCopyOnRead^Read_1/ReadVariableOp^Read_10/DisableCopyOnRead^Read_10/ReadVariableOp^Read_11/DisableCopyOnRead^Read_11/ReadVariableOp^Read_12/DisableCopyOnRead^Read_12/ReadVariableOp^Read_13/DisableCopyOnRead^Read_13/ReadVariableOp^Read_14/DisableCopyOnRead^Read_14/ReadVariableOp^Read_15/DisableCopyOnRead^Read_15/ReadVariableOp^Read_16/DisableCopyOnRead^Read_16/ReadVariableOp^Read_2/DisableCopyOnRead^Read_2/ReadVariableOp^Read_3/DisableCopyOnRead^Read_3/ReadVariableOp^Read_4/DisableCopyOnRead^Read_4/ReadVariableOp^Read_5/DisableCopyOnRead^Read_5/ReadVariableOp^Read_6/DisableCopyOnRead^Read_6/ReadVariableOp^Read_7/DisableCopyOnRead^Read_7/ReadVariableOp^Read_8/DisableCopyOnRead^Read_8/ReadVariableOp^Read_9/DisableCopyOnRead^Read_9/ReadVariableOp*
_output_shapes
 "#
identity_35Identity_35:output:0*(
_construction_contextkEagerRuntime*9
_input_shapes(
&: : : : : : : : : : : : : : : : : : : 2(
MergeV2CheckpointsMergeV2Checkpoints20
Read/DisableCopyOnReadRead/DisableCopyOnRead2*
Read/ReadVariableOpRead/ReadVariableOp24
Read_1/DisableCopyOnReadRead_1/DisableCopyOnRead2.
Read_1/ReadVariableOpRead_1/ReadVariableOp26
Read_10/DisableCopyOnReadRead_10/DisableCopyOnRead20
Read_10/ReadVariableOpRead_10/ReadVariableOp26
Read_11/DisableCopyOnReadRead_11/DisableCopyOnRead20
Read_11/ReadVariableOpRead_11/ReadVariableOp26
Read_12/DisableCopyOnReadRead_12/DisableCopyOnRead20
Read_12/ReadVariableOpRead_12/ReadVariableOp26
Read_13/DisableCopyOnReadRead_13/DisableCopyOnRead20
Read_13/ReadVariableOpRead_13/ReadVariableOp26
Read_14/DisableCopyOnReadRead_14/DisableCopyOnRead20
Read_14/ReadVariableOpRead_14/ReadVariableOp26
Read_15/DisableCopyOnReadRead_15/DisableCopyOnRead20
Read_15/ReadVariableOpRead_15/ReadVariableOp26
Read_16/DisableCopyOnReadRead_16/DisableCopyOnRead20
Read_16/ReadVariableOpRead_16/ReadVariableOp24
Read_2/DisableCopyOnReadRead_2/DisableCopyOnRead2.
Read_2/ReadVariableOpRead_2/ReadVariableOp24
Read_3/DisableCopyOnReadRead_3/DisableCopyOnRead2.
Read_3/ReadVariableOpRead_3/ReadVariableOp24
Read_4/DisableCopyOnReadRead_4/DisableCopyOnRead2.
Read_4/ReadVariableOpRead_4/ReadVariableOp24
Read_5/DisableCopyOnReadRead_5/DisableCopyOnRead2.
Read_5/ReadVariableOpRead_5/ReadVariableOp24
Read_6/DisableCopyOnReadRead_6/DisableCopyOnRead2.
Read_6/ReadVariableOpRead_6/ReadVariableOp24
Read_7/DisableCopyOnReadRead_7/DisableCopyOnRead2.
Read_7/ReadVariableOpRead_7/ReadVariableOp24
Read_8/DisableCopyOnReadRead_8/DisableCopyOnRead2.
Read_8/ReadVariableOpRead_8/ReadVariableOp24
Read_9/DisableCopyOnReadRead_9/DisableCopyOnRead2.
Read_9/ReadVariableOpRead_9/ReadVariableOp:?;

_output_shapes
: 
!
_user_specified_name	Const_2:-)
'
_user_specified_namelatent/bias_1:/+
)
_user_specified_namelatent/kernel_1:1-
+
_user_specified_nameenc_dense2/bias_1:1-
+
_user_specified_nameenc_dense1/bias_1:3/
-
_user_specified_nameenc_dense2/kernel_1:3/
-
_user_specified_nameenc_dense1/kernel_1:($
"
_user_specified_name
Variable:*
&
$
_user_specified_name
Variable_1:*	&
$
_user_specified_name
Variable_2:*&
$
_user_specified_name
Variable_3:*&
$
_user_specified_name
Variable_4:*&
$
_user_specified_name
Variable_5:*&
$
_user_specified_name
Variable_6:*&
$
_user_specified_name
Variable_7:*&
$
_user_specified_name
Variable_8:*&
$
_user_specified_name
Variable_9:+'
%
_user_specified_nameVariable_10:C ?

_output_shapes
: 
%
_user_specified_namefile_prefix
�
�
-__inference_signature_wrapper___call___569917
input_layer
unknown
	unknown_0
	unknown_1:
	unknown_2:
	unknown_3:
	unknown_4:
	unknown_5:
	unknown_6:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinput_layerunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6*
Tin
2	*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*(
_read_only_resource_inputs

*2
config_proto" 

CPU

GPU 2J 8� �J *$
fR
__inference___call___569874o
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������<
NoOpNoOp^StatefulPartitionedCall*
_output_shapes
 "
identityIdentity:output:0*(
_construction_contextkEagerRuntime*F
_input_shapes5
3:���������::: : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:&"
 
_user_specified_name569913:&"
 
_user_specified_name569911:&"
 
_user_specified_name569909:&"
 
_user_specified_name569907:&"
 
_user_specified_name569905:&"
 
_user_specified_name569903:$ 

_output_shapes

::$ 

_output_shapes

::T P
'
_output_shapes
:���������
%
_user_specified_nameinput_layer
�
�
-__inference_signature_wrapper___call___569896
input_layer
unknown
	unknown_0
	unknown_1:
	unknown_2:
	unknown_3:
	unknown_4:
	unknown_5:
	unknown_6:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinput_layerunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6*
Tin
2	*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*(
_read_only_resource_inputs

*2
config_proto" 

CPU

GPU 2J 8� �J *$
fR
__inference___call___569874o
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������<
NoOpNoOp^StatefulPartitionedCall*
_output_shapes
 "
identityIdentity:output:0*(
_construction_contextkEagerRuntime*F
_input_shapes5
3:���������::: : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:&"
 
_user_specified_name569892:&"
 
_user_specified_name569890:&"
 
_user_specified_name569888:&"
 
_user_specified_name569886:&"
 
_user_specified_name569884:&"
 
_user_specified_name569882:$ 

_output_shapes

::$ 

_output_shapes

::T P
'
_output_shapes
:���������
%
_user_specified_nameinput_layer"�L
saver_filename:0StatefulPartitionedCall_2:0StatefulPartitionedCall_38"
saved_model_main_op

NoOp*>
__saved_model_init_op%#
__saved_model_init_op

NoOp*�
serve�
9
input_layer*
serve_input_layer:0���������<
output_00
StatefulPartitionedCall:0���������tensorflow/serving/predict*�
serving_default�
C
input_layer4
serving_default_input_layer:0���������>
output_02
StatefulPartitionedCall_1:0���������tensorflow/serving/predict:�
�
	variables
trainable_variables
non_trainable_variables
_all_variables
_misc_assets
	serve

signatures"
_generic_user_object
n
0
	1

2
3
4
5
6
7
8
9
10"
trackable_list_wrapper
J
0
1
2
3
4
5"
trackable_list_wrapper
C
0
	1

2
3
4"
trackable_list_wrapper
J
0
1
2
3
4
5"
trackable_list_wrapper
 "
trackable_list_wrapper
�
trace_02�
__inference___call___569874�
���
FullArgSpec
args�

jargs_0
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� **�'
%�"
input_layer���������ztrace_0
7
	serve
serving_default"
signature_map
:2normalization/mean
": 2normalization/variance
:	 2normalization/count
#:!2enc_dense1/kernel
:2enc_dense1/bias
/:-	2#seed_generator/seed_generator_state
#:!2enc_dense2/kernel
:2enc_dense2/bias
1:/	2%seed_generator_1/seed_generator_state
:2latent/kernel
:2latent/bias
#:!2enc_dense1/kernel
#:!2enc_dense2/kernel
:2enc_dense1/bias
:2enc_dense2/bias
:2latent/kernel
:2latent/bias
�
	capture_0
	capture_1B�
__inference___call___569874input_layer"�
���
FullArgSpec
args�

jargs_0
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 z	capture_0z	capture_1
�
	capture_0
	capture_1B�
-__inference_signature_wrapper___call___569896input_layer"�
���
FullArgSpec
args� 
varargs
 
varkw
 
defaults
  

kwonlyargs�
jinput_layer
kwonlydefaults
 
annotations� *
 z	capture_0z	capture_1
�
	capture_0
	capture_1B�
-__inference_signature_wrapper___call___569917input_layer"�
���
FullArgSpec
args� 
varargs
 
varkw
 
defaults
  

kwonlyargs�
jinput_layer
kwonlydefaults
 
annotations� *
 z	capture_0z	capture_1
!J	
Const_1jtf.TrackableConstant
J
Constjtf.TrackableConstant�
__inference___call___569874c4�1
*�'
%�"
input_layer���������
� "!�
unknown����������
-__inference_signature_wrapper___call___569896�C�@
� 
9�6
4
input_layer%�"
input_layer���������"3�0
.
output_0"�
output_0����������
-__inference_signature_wrapper___call___569917�C�@
� 
9�6
4
input_layer%�"
input_layer���������"3�0
.
output_0"�
output_0���������