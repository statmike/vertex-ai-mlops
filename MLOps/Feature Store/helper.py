# modified from the excellent work of Elia Secchi

from typing import Dict, Optional, List, Any, Union
import asyncio
import logging
from google.cloud import aiplatform
import vertexai
from vertexai.resources.preview.feature_store import FeatureView

# Configure logging to display informative messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureViewNotFound(Exception):
    """Custom exception raised when a feature view is not found."""
    pass

def find_feature_view(feature_online_store_id: str, feature_view_id: str) -> Optional[FeatureView]:
    """
    Finds a feature view object given its ID and the feature online store ID.

    This function iterates through the list of feature views in the specified
    online store and returns the one that matches the given ID.

    Args:
        feature_online_store_id: The ID of the feature online store.
        feature_view_id: The ID of the feature view to find.

    Returns:
        The found feature view object, or None if it's not found.
    """
    try:
        # Retrieve all feature views from the specified online store
        fv_list = FeatureView.list(feature_online_store_id=feature_online_store_id)
        # Find the feature view with the matching ID
        return next((fv for fv in fv_list if fv.name == feature_view_id), None)
    except Exception as e:
        logger.error(f"Failed to list feature views for store '{feature_online_store_id}': {e}")
        raise

class OnlineStoreReader:
    """
    A class for reading online features from a Vertex AI Feature Store.

    This class provides an interface to asynchronously fetch features from
    one or more feature views within a single online store. It includes
    caching for feature view objects to optimize performance.

    Example:
        # Initialize the reader with your feature store ID
        online_store_reader = OnlineStoreReader("my_feature_store")

        # Define the entities to fetch
        ids_to_fetch = [
            {"feature_view": "user_profile_view", "key": ["user123"]},
            {"feature_view": "product_details_view", "key": ["product456"]}
        ]

        # Fetch features, returning a list of dictionaries (default behavior)
        features_list = online_store_reader.get_online_features(ids=ids_to_fetch)
        print(features_list)
        # Expected output:
        # [{'user_feature_1': 'value1'}, {'product_feature_1': 'valueA'}]

        # Fetch features and combine them into a single dictionary
        combined_features = online_store_reader.get_online_features(
            ids=ids_to_fetch,
            combine_results=True
        )
        print(combined_features)
        # Expected output:
        # {'user_feature_1': 'value1', 'product_feature_1': 'valueA'}
    """

    def __init__(self, feature_online_store_id: str, feature_view_cache: Optional[Dict[str, FeatureView]] = None):
        """
        Initializes the OnlineStoreReader.

        Args:
            feature_online_store_id: The ID of the feature online store.
            feature_view_cache: An optional dictionary to cache feature view objects.
        """
        self.feature_online_store_id = feature_online_store_id
        self.feature_view_cache = feature_view_cache if feature_view_cache is not None else {}

    def get_feature_view(self, feature_view_id: str) -> FeatureView:
        """
        Retrieves a feature view by its ID, using a cache to avoid repeated lookups.

        Args:
            feature_view_id: The ID of the feature view to retrieve.

        Returns:
            The requested feature view object.

        Raises:
            FeatureViewNotFound: If the feature view cannot be found.
        """
        # Return the feature view from the cache if it's already there
        if feature_view_id in self.feature_view_cache:
            return self.feature_view_cache[feature_view_id]

        logger.info(f"Fetching feature view '{feature_view_id}' from the store.")
        try:
            # Find the feature view and raise an error if it's not found
            feature_view = find_feature_view(
                feature_online_store_id=self.feature_online_store_id,
                feature_view_id=feature_view_id
            )
            if not feature_view:
                raise FeatureViewNotFound(f"Feature view '{feature_view_id}' not found in store '{self.feature_online_store_id}'.")
            
            # Cache the feature view for future use
            self.feature_view_cache[feature_view_id] = feature_view
            return feature_view
        except Exception as e:
            logger.error(f"Error fetching feature view '{feature_view_id}': {e}")
            raise

    def get_online_features(self, ids: List[Dict[str, Any]], combine_results: bool = False, exclude_feature_timestamp: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Synchronous wrapper for fetching online features.

        This method provides a simple way to call the asynchronous feature
        fetching logic from a synchronous context.

        Args:
            ids: A list of dictionaries, each specifying a feature view and an entity key.
            combine_results: If True, merges results into a single dictionary.
            exclude_feature_timestamp: If True, the 'feature_timestamp' field is omitted.

        Returns:
            A list of dictionaries (default) or a single merged dictionary if
            combine_results is True.
        """
        # Ensure there is an event loop running, or create a new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._async_get_online_features(ids, combine_results, exclude_feature_timestamp))

    async def _async_get_online_features(self, ids: List[Dict[str, Any]], combine_results: bool, exclude_feature_timestamp: bool) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Asynchronously fetches online features for multiple entities.

        This method concurrently fetches features for all the provided entities,
        which can significantly improve performance for batch requests.

        Args:
            ids: A list of dictionaries with feature view and entity key information.
            combine_results: If True, merges results into a single dictionary.
            exclude_feature_timestamp: Controls the inclusion of the feature timestamp.

        Returns:
            A list of feature dictionaries, or a single merged dictionary.
        """
        # Create a list of tasks to be executed concurrently
        tasks = [
            self._get_entity_features(
                id_dict['feature_view'],
                id_dict['key'],
                exclude_feature_timestamp
            )
            for id_dict in ids
        ]
        # Wait for all feature fetching tasks to complete
        results = await asyncio.gather(*tasks)

        if combine_results:
            merged_dict = {}
            for d in results:
                merged_dict.update(d)
            return merged_dict

        return results

    async def _get_entity_features(self, feature_view_id: str, key: List[str], exclude_feature_timestamp: bool) -> Dict[str, Any]:
        """
        Asynchronously fetches features for a single entity.

        Args:
            feature_view_id: The ID of the feature view to read from.
            key: The entity key for which to fetch features.
            exclude_feature_timestamp: If True, the feature timestamp is excluded.

        Returns:
            A dictionary of features for the specified entity.
        """
        try:
            # Retrieve the feature view object
            feature_view = self.get_feature_view(feature_view_id)
            # Asynchronously read the feature data
            features = await asyncio.to_thread(feature_view.read, key=key)
            
            # Return an empty dictionary if no features are found
            if not features or 'features' not in features.to_dict():
                logger.warning(f"No features found for key '{key}' in view '{feature_view_id}'.")
                return {}

            feature_dict = {}
            # Process each feature and add it to the dictionary
            for feature in features.to_dict()['features']:
                feature_name = feature.get('name')
                if exclude_feature_timestamp and feature_name == 'feature_timestamp':
                    continue
                if feature_name:
                    feature_dict[feature_name] = self._parse_feature_value(feature.get('value'))

            return feature_dict
        except FeatureViewNotFound:
            # Handle cases where the feature view doesn't exist
            logger.error(f"Could not fetch features for key '{key}' because view '{feature_view_id}' was not found.")
            return {}
        except Exception as e:
            # Log any other errors that occur during feature fetching
            logger.error(f"Error fetching features for key '{key}' from view '{feature_view_id}': {e}")
            return {}

    @staticmethod
    def _parse_feature_value(feature_value: Optional[Dict[str, Any]]) -> Any:
        """
        Parses a feature value from the API response format.

        This method intelligently extracts the value from the nested dictionary
        structure returned by the Vertex AI API.

        Args:
            feature_value: The feature value dictionary from the API response.

        Returns:
            The parsed feature value.
        """
        if feature_value is None:
            return None
            
        # Iterate through possible value types and return the first one found
        for key, value in feature_value.items():
            if 'value' in key.lower():
                # Attempt to convert to a more specific type if possible
                if 'int64' in key.lower() or 'int32' in key.lower():
                    return int(value)
                return value
        # Fallback to a string representation if no value is found
        return str(feature_value)

# --- Example Usage ---
# Replace with your actual Project ID, Location, and Feature Online Store ID
PROJECT_ID = 'your-gcp-project-id'
LOCATION = 'your-gcp-location'
FEATURE_ONLINE_STORE_ID = 'your-feature-online-store-id'

# Initialize the Vertex AI client
# Make sure you are authenticated with GCP, e.g., via `gcloud auth application-default login`
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # --- Mocking for demonstration purposes ---
    # In a real scenario, you would not mock these. This is to make the example runnable.
    entity_id_user = 'user123'
    entity_id_product = 'prod456'
    
    # Instantiate the reader
    online_store_reader = OnlineStoreReader(feature_online_store_id=FEATURE_ONLINE_STORE_ID)

    # Define the features to fetch
    ids_to_fetch = [
        {'feature_view': 'view_1', 'key': [entity_id_user,]},
        {'feature_view': 'view_2', 'key': [entity_id_product,]},
        {'feature_view': 'non_existent_view', 'key': ['some_id']} # Example for a non-existent view
    ]

    # Fetch the online features as a list (default)
    print("Fetching online features (default list output)...")
    features_list_result = online_store_reader.get_online_features(ids=ids_to_fetch)
    
    print("\n--- Fetched Features (List) ---")
    print(features_list_result)
    print("-----------------------------\n")

    # Fetch the online features and combine them into a single dictionary
    print("Fetching online features (combined dictionary output)...")
    combined_features_result = online_store_reader.get_online_features(ids=ids_to_fetch, combine_results=True)

    print("\n--- Fetched Features (Combined) ---")
    print(combined_features_result)
    print("---------------------------------\n")

except Exception as e:
    logger.error(f"An error occurred during Vertex AI initialization or feature fetching: {e}")
    logger.info("Please ensure you have set your PROJECT_ID, LOCATION, and FEATURE_ONLINE_STORE_ID correctly.")

