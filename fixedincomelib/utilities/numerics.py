import copy
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

class InterpMethod(Enum):

    PIECEWISE_CONSTANT_LEFT_CONTINUOUS = 'PIECEWISE_CONSTANT_LEFT_CONTINUOUS'
    LINEAR = 'LINEAR'

    @classmethod
    def from_string(cls, value: str) -> 'InterpMethod':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

class ExtrapMethod(Enum):
    
    FLAT = 'FLAT'
    LINEAR = 'LINEAR'

    @classmethod
    def from_string(cls, value: str) -> 'ExtrapMethod':
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid token: {value}")

    def to_string(self) -> str:
        return self.value

class Interpolator1D(ABC):

    def __init__(self,
                 axis1 : np.ndarray, 
                 values : np.ndarray, 
                 interpolation_method : InterpMethod,
                 extrpolation_method : ExtrapMethod) -> None:

        self.axis1_ = axis1
        self.values_ = values
        self.interp_method_ = interpolation_method
        self.extrap_method_ = extrpolation_method
        self.length_ = len(self.axis1)

    @abstractmethod
    def interpolate(self, x : float) -> float:
        pass

    @abstractmethod
    def integrate(self, start_x : float, end_x : float):
        pass

    @abstractmethod
    def gradient_wrt_ordinate(self, x : float):
        pass

    @abstractmethod
    def gradient_of_integrated_value_wrt_ordinate(self, start_x : float, end_x : float):
        pass
    
    @property
    def axis1(self) -> np.ndarray:
        return self.axis1_
    
    @property
    def values(self) -> np.ndarray:
        return self.values_
    
    @property
    def length(self) -> int:
        return self.length_

    @property
    def interp_method(self) -> str:
        return self.interp_method_.to_string()
    
    @property
    def extrap_method(self) -> str:
        return self.extrap_method_.to_string()

class Interpolator1DPCP(Interpolator1D):

    def __init__(
            self, 
            axis1: np.ndarray, 
            values: np.ndarray, 
            extrpolation_method: ExtrapMethod) -> None:
        super().__init__(axis1, values, InterpMethod.LINEAR, extrpolation_method)
        assert self.extrap_method_ == ExtrapMethod.FLAT

    def interpolate(self, x: float) -> float:
        ### TODO
        axis = self.axis1_
        values = self.values_
        n = self.length_

        if x < axis[0]:
            return float(values[0])
        
        for i in range(n - 1):
            if axis[i] <= x < axis[i + 1]:
                return float(values[i + 1])
            
        return float(values[n - 1])

    


    def integrate(self, start_x : float, end_x : float):
        ### TODO
        axis = self.axis1_
        values = self.values_
        n = self.length_

        if start_x == end_x:
            return 0.0
        
        
        if end_x < axis[0]:
            return float(values[0]*(end_x - start_x))
        if start_x > axis[-1]:
            return float(values[-1]*(end_x-start_x))
        if start_x < axis[0]:
            total = values[0]*(axis[0] - start_x)
            for i in range(n-1):
                if axis[i] <= end_x < axis[i+1]:
                    total += values[i+1]*(end_x -axis[i])
                    return float(total)
                total+=values[i+1]*(axis[i+1]-axis[i])
        
            total += values[n-1]*(end_x-axis[n-1]) 
            return float(total)
        else:
            total= 0.0
            index4end = 0
            for i in range(n-1):
                if axis[i] <= start_x < axis[i + 1]:                
                    if end_x <= axis[i + 1]:
                        return float( values[i+1]*(end_x - start_x)),1
                    total += values[i+1]*(axis[i + 1] - start_x)
                    index4end = i+1
                    break
            for i in range(index4end,n-1):
                if axis[i] <= end_x < axis[i+1]:
                    total += values[i+1]*(end_x -axis[i])
                    return float(total)
                else:
                    total+=values[i+1]*(axis[i+1]-axis[i])
            
            total += values[n-1]*(end_x-axis[n-1])

            return float(total)
        
                
                

    def gradient_wrt_ordinate(self, x : float):
        ### TODO
        axis = self.axis1_
        n = self.length_
        grad = np.zeros(n)

       
        if x < axis[0]:
            grad[0] = 1.0
            return grad

        for i in range(n - 1):
            if axis[i] <= x < axis[i + 1]:
                grad[i + 1] = 1.0
                return grad

        grad[n - 1] = 1.0
        return grad
        

    def gradient_of_integrated_value_wrt_ordinate(self, start_x : float, end_x : float):
        ### TODO
        
        if start_x == end_x:
            return np.zeros(self.length_)

        sign = 1.0
        if end_x < start_x:
            start_x, end_x = end_x, start_x
            sign = -1.0

        axis = self.axis1_
        n = self.length_
        overlap = np.zeros(n)

        # Left wing: 
        if start_x < axis[0]:
            left = start_x
            right = min(end_x, axis[0])
            if right > left:
                overlap[0] = right - left

        # Interior buckets: 
        for i in range(n - 1):
            left = max(start_x, axis[i])
            right = min(end_x, axis[i + 1])
            if right > left:
                overlap[i + 1] += right - left

        # Right wing: 
        if end_x > axis[-1]:
            left = max(start_x, axis[-1])
            right = end_x
            if right > left:
                overlap[n - 1] += right - left

        return overlap * sign   

class InterpolatorFactory:

    @staticmethod
    def create_1d_interpolator(axis1 : np.ndarray | List, 
                               values : np.ndarray | List, 
                               interpolation_method : InterpMethod,
                               extrpolation_method : ExtrapMethod):


        axis1_ = copy.deepcopy(axis1)
        values_ = copy.deepcopy(values)
        if isinstance(axis1_, list):
            axis1_ = np.array(axis1_)
        if isinstance(values_, list):
            values_ = np.array(values_)
        assert len(axis1_.shape) == 1 and len(values_.shape) == 1
        assert len(axis1_) == len(values_)
        assert np.all(np.diff(axis1_) >= 0)
    
        if interpolation_method == InterpMethod.PIECEWISE_CONSTANT_LEFT_CONTINUOUS:
            return Interpolator1DPCP(axis1_, values_, extrpolation_method)
        else:
            raise Exception('Currently only support PCP interpolation')
