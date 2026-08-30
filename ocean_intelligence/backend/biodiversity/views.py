from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from biodiversity.models import BiodiversityIndicator
from biodiversity.serializers import BiodiversityIndicatorSerializer
from biodiversity.risk_analysis import BiodiversityRiskAnalyzer

class BiodiversityIndicatorViewSet(viewsets.ModelViewSet):
    queryset = BiodiversityIndicator.objects.all().order_by('-risk_score')
    serializer_class = BiodiversityIndicatorSerializer

    @action(detail=False, methods=['post'], url_path='recalculate')
    def recalculate(self, request):
        """Forces recalculation of biodiversity indicators for all regions."""
        analyzer = BiodiversityRiskAnalyzer()
        try:
            count = analyzer.calculate_region_biodiversity()
            return Response(
                {"message": f"Successfully recalculated biodiversity indicators for {count} regions."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to recalculate: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
